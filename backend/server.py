"""MACHBAR API with SQLite and validated photo uploads."""
import base64
import binascii
import io
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import sqlite3
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DIST = ROOT.parent / 'dist'
DB = Path(os.environ.get('MACHBAR_DB', ROOT / 'machbar.db'))
HOST = os.environ.get('MACHBAR_HOST', '127.0.0.1')
PORT = int(os.environ.get('MACHBAR_PORT', '8000'))
STATUSES = {'open', 'assigned', 'in_progress', 'done'}
MAX_PHOTOS = 6
MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_JOB_PAYLOAD = 42 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect():
    con = sqlite3.connect(DB, factory=ClosingConnection)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
            company TEXT NOT NULL DEFAULT '', role TEXT NOT NULL CHECK(role IN ('customer','provider','admin')),
            salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES users(id),
            provider_id INTEGER REFERENCES users(id), category TEXT NOT NULL, title TEXT NOT NULL,
            description TEXT NOT NULL, postal_code TEXT NOT NULL, city TEXT NOT NULL,
            address TEXT NOT NULL DEFAULT '', desired_date TEXT NOT NULL DEFAULT '',
            contact_name TEXT NOT NULL, contact_email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_jobs_customer ON jobs(customer_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_provider ON jobs(provider_id);
        CREATE TABLE IF NOT EXISTS job_photos (
            id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            name TEXT NOT NULL, mime TEXT NOT NULL, data BLOB NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_photos_job ON job_photos(job_id);
        ''')
        if 'details_json' not in {row['name'] for row in db.execute('PRAGMA table_info(jobs)')}:
            db.execute("ALTER TABLE jobs ADD COLUMN details_json TEXT NOT NULL DEFAULT '{}'")
        admin_email = os.environ.get('MACHBAR_ADMIN_EMAIL', '').strip().lower()
        admin_password = os.environ.get('MACHBAR_ADMIN_PASSWORD', '')
        if admin_email and admin_password and not db.execute('SELECT id FROM users WHERE email=?', (admin_email,)).fetchone():
            salt = secrets.token_hex(16)
            db.execute('INSERT INTO users(email,name,company,role,salt,password_hash) VALUES (?,?,?,?,?,?)',
                       (admin_email, 'MACHBAR Admin', 'MACHBAR', 'admin', salt, hash_password(admin_password, salt)))


def hash_password(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1).hex()


def public_user(row):
    return {key: row[key] for key in ('id', 'email', 'name', 'company', 'role')}


def public_job(row, db):
    job = dict(row)
    job['details'] = json.loads(job.pop('details_json'))
    job['photos'] = [{'id': photo['id'], 'name': photo['name'], 'url': f"/api/jobs/{job['id']}/photos/{photo['id']}"}
                     for photo in db.execute('SELECT id,name FROM job_photos WHERE job_id=? ORDER BY id', (job['id'],))]
    return job


def request_details(value):
    if not isinstance(value, dict):
        raise ValueError('Ungültige Auftragsdetails.')
    limits = {'amount': 40, 'detail_label': 150, 'detail': 150, 'timing': 100, 'destination': 150, 'notes': 2000}
    result = {}
    for key, limit in limits.items():
        field = value.get(key, '')
        if not isinstance(field, str) or len(field) > limit:
            raise ValueError('Ungültige Auftragsdetails.')
        result[key] = field.strip()
    work = value.get('work', [])
    if not isinstance(work, list) or len(work) > 50 or any(not isinstance(item, str) or len(item) > 150 for item in work):
        raise ValueError('Ungültige Auswahl der Arbeiten.')
    result['work'] = work
    if 'services' in value:
        services = value['services']
        if not isinstance(services, list) or not 1 <= len(services) <= 50 or any(not isinstance(item, str) or not item.strip() or len(item) > 150 for item in services):
            raise ValueError('Ungültige Leistungsauswahl.')
        result['services'] = list(dict.fromkeys(services))
    if 'scopes' in value:
        scopes = value['scopes']
        if not isinstance(scopes, list) or len(scopes) > 10:
            raise ValueError('Ungültige Angaben zum Umfang.')
        result['scopes'] = []
        for scope in scopes:
            if not isinstance(scope, dict):
                raise ValueError('Ungültige Angaben zum Umfang.')
            clean = {}
            for key, limit in {'group': 80, 'amount': 40, 'detail_label': 150, 'detail': 150}.items():
                field = scope.get(key, '')
                if not isinstance(field, str) or len(field) > limit:
                    raise ValueError('Ungültige Angaben zum Umfang.')
                clean[key] = field.strip()
            result['scopes'].append(clean)
    return json.dumps(result, ensure_ascii=False) if value else '{}'


def prepare_photos(photos):
    if not isinstance(photos, list) or len(photos) > MAX_PHOTOS:
        raise ValueError('Bitte höchstens 6 Fotos hochladen.')
    prepared = []
    for photo in photos:
        if not isinstance(photo, dict) or not isinstance(photo.get('name'), str) or not 1 <= len(photo['name']) <= 150:
            raise ValueError('Ungültiger Foto-Dateiname.')
        data = photo.get('data', '')
        if not isinstance(data, str) or len(data) > (MAX_PHOTO_BYTES + 2) // 3 * 4 + 40:
            raise ValueError('Ein Foto darf höchstens 5 MB groß sein.')
        prefix, separator, encoded = data.partition(',')
        if not separator or prefix not in ('data:image/jpeg;base64', 'data:image/png;base64', 'data:image/webp;base64'):
            raise ValueError('Bitte JPG-, PNG- oder WebP-Fotos hochladen.')
        try:
            raw = base64.b64decode(encoded, validate=True)
            if not raw or len(raw) > MAX_PHOTO_BYTES:
                raise ValueError('Ein Foto darf höchstens 5 MB groß sein.')
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(raw)) as image:
                    if image.format not in ('JPEG', 'PNG', 'WEBP'):
                        raise ValueError('Bitte JPG-, PNG- oder WebP-Fotos hochladen.')
                    image.verify()
                with Image.open(io.BytesIO(raw)) as image:
                    normalized = ImageOps.exif_transpose(image)
                    normalized.thumbnail((2400, 2400))
                    rgba = normalized.convert('RGBA')
                    clean = Image.new('RGB', rgba.size, 'white')
                    clean.paste(rgba, mask=rgba.getchannel('A'))
                    output = io.BytesIO()
                    clean.save(output, format='JPEG', quality=85)
            prepared.append((photo['name'], 'image/jpeg', output.getvalue()))
        except (UnidentifiedImageError, OSError, binascii.Error, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ValueError('Ein Foto ist beschädigt oder hat mehr als 20 Megapixel. Bitte wähle eine kleinere JPG-, PNG- oder WebP-Datei.') from None
    return prepared


def can_view_job(user, job):
    return user and (user['role'] == 'admin' or
        (user['role'] == 'provider' and job['provider_id'] == user['id']) or
        (user['role'] == 'customer' and (job['customer_id'] == user['id'] or
         (job['customer_id'] is None and job['contact_email'] == user['email']))))


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def payload(self, limit=50000):
        size = int(self.headers.get('Content-Length', '0'))
        if size < 0 or size > limit:
            raise ValueError('Anfrage ist zu groß.')
        data = json.loads(self.rfile.read(size) or b'{}')
        if not isinstance(data, dict):
            raise ValueError('Ungültige Eingabe.')
        return data

    def user(self, db):
        auth = self.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return None
        token_hash = hashlib.sha256(auth[7:].encode()).hexdigest()
        return db.execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?',
                          (token_hash, datetime.now(timezone.utc).isoformat())).fetchone()

    def route(self, method):
        path = urlparse(self.path).path.rstrip('/') or '/'
        if not path.startswith('/api/') and path != '/api':
            if method == 'GET':
                return self.static(path)
            return self.respond(404, {'error': 'Nicht gefunden.'})
        try:
            with connect() as db:
                user = self.user(db)
                if method == 'GET' and path == '/api/health':
                    return self.respond(200, {'ok': True})
                if method == 'POST' and path == '/api/auth/register':
                    data = self.payload()
                    email = str(data.get('email', '')).strip().lower()
                    name = str(data.get('name', '')).strip()
                    password = str(data.get('password', ''))
                    role = data.get('role', 'customer')
                    if not email or '@' not in email or len(email) > 254 or not name or len(name) > 100 or len(password) < 8 or role not in ('customer', 'provider'):
                        return self.respond(400, {'error': 'Bitte gültige Angaben und ein Passwort mit mindestens 8 Zeichen eingeben.'})
                    salt = secrets.token_hex(16)
                    try:
                        cur = db.execute('INSERT INTO users(email,name,company,role,salt,password_hash) VALUES (?,?,?,?,?,?)',
                                         (email, name, str(data.get('company', ''))[:120], role, salt, hash_password(password, salt)))
                    except sqlite3.IntegrityError:
                        return self.respond(409, {'error': 'Diese E-Mail-Adresse ist bereits registriert.'})
                    created = db.execute('SELECT * FROM users WHERE id=?', (cur.lastrowid,)).fetchone()
                    return self.login_response(db, created)
                if method == 'POST' and path == '/api/auth/login':
                    data = self.payload()
                    found = db.execute('SELECT * FROM users WHERE email=?', (str(data.get('email', '')).strip().lower(),)).fetchone()
                    if not found or not hmac.compare_digest(found['password_hash'], hash_password(str(data.get('password', '')), found['salt'])):
                        return self.respond(401, {'error': 'E-Mail oder Passwort ist falsch.'})
                    return self.login_response(db, found)
                if method == 'GET' and path == '/api/auth/me':
                    return self.respond(200, {'user': public_user(user)}) if user else self.respond(401, {'error': 'Bitte anmelden.'})
                if method == 'GET' and path == '/api/providers':
                    if not user or user['role'] != 'admin':
                        return self.respond(403, {'error': 'Keine Berechtigung.'})
                    providers = [public_user(x) for x in db.execute("SELECT * FROM users WHERE role='provider' ORDER BY company,name")]
                    return self.respond(200, {'providers': providers})
                if method == 'POST' and path == '/api/jobs':
                    data = self.payload(MAX_JOB_PAYLOAD)
                    if user and user['role'] != 'customer':
                        return self.respond(403, {'error': 'Nur Kunden können Anfragen stellen.'})
                    category = str(data.get('category', '')).strip()[:80]
                    title = str(data.get('title', '')).strip()[:120]
                    description = str(data.get('description', '')).strip()[:5000]
                    postal_code = str(data.get('postal_code', '')).strip()
                    city = str(data.get('city', '')).strip()[:100]
                    contact_name = user['name'] if user else str(data.get('contact_name', '')).strip()[:100]
                    contact_email = user['email'] if user else str(data.get('contact_email', '')).strip().lower()[:254]
                    if not category or not title or len(description) < 15 or len(postal_code) != 5 or not postal_code.isdigit() or not city or not contact_name or '@' not in contact_email:
                        return self.respond(400, {'error': 'Bitte alle Pflichtfelder korrekt ausfüllen.'})
                    details_json = request_details(data.get('details', {}))
                    photos = prepare_photos(data.get('photos', []))
                    cur = db.execute('''INSERT INTO jobs(customer_id,category,title,description,postal_code,city,address,desired_date,contact_name,contact_email,details_json)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (user['id'] if user else None, category, title, description, postal_code, city,
                        str(data.get('address', '')).strip()[:200], str(data.get('desired_date', '')).strip()[:20], contact_name, contact_email, details_json))
                    db.executemany('INSERT INTO job_photos(job_id,name,mime,data) VALUES (?,?,?,?)',
                                   [(cur.lastrowid, name, mime, photo_data) for name, mime, photo_data in photos])
                    db.commit()
                    return self.respond(201, {'id': cur.lastrowid, 'message': 'Anfrage eingegangen.'})
                if method == 'GET' and path.startswith('/api/jobs/') and '/photos/' in path:
                    parts = path.split('/')
                    if len(parts) != 6 or not parts[3].isdigit() or not parts[5].isdigit():
                        return self.respond(404, {'error': 'Foto nicht gefunden.'})
                    if not user:
                        return self.respond(401, {'error': 'Bitte anmelden.'})
                    job = db.execute('SELECT * FROM jobs WHERE id=?', (int(parts[3]),)).fetchone()
                    if not job or not can_view_job(user, job):
                        return self.respond(403, {'error': 'Keine Berechtigung.'})
                    photo = db.execute('SELECT mime,data FROM job_photos WHERE id=? AND job_id=?', (int(parts[5]), job['id'])).fetchone()
                    if not photo:
                        return self.respond(404, {'error': 'Foto nicht gefunden.'})
                    self.send_response(200)
                    self.send_header('Content-Type', photo['mime'])
                    self.send_header('Content-Length', str(len(photo['data'])))
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('X-Content-Type-Options', 'nosniff')
                    self.end_headers()
                    self.wfile.write(photo['data'])
                    return
                if method == 'GET' and path == '/api/jobs':
                    if not user:
                        return self.respond(401, {'error': 'Bitte anmelden.'})
                    if user['role'] == 'admin':
                        rows = db.execute('SELECT * FROM jobs ORDER BY id DESC').fetchall()
                    elif user['role'] == 'provider':
                        rows = db.execute('SELECT * FROM jobs WHERE provider_id=? ORDER BY id DESC', (user['id'],)).fetchall()
                    else:
                        rows = db.execute('SELECT * FROM jobs WHERE customer_id=? OR (customer_id IS NULL AND contact_email=?) ORDER BY id DESC', (user['id'], user['email'])).fetchall()
                    return self.respond(200, {'jobs': [public_job(row, db) for row in rows]})
                if method == 'PATCH' and path.startswith('/api/jobs/'):
                    if not user:
                        return self.respond(401, {'error': 'Bitte anmelden.'})
                    try:
                        job_id = int(path.split('/')[-1])
                    except ValueError:
                        return self.respond(404, {'error': 'Auftrag nicht gefunden.'})
                    job = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
                    if not job:
                        return self.respond(404, {'error': 'Auftrag nicht gefunden.'})
                    data = self.payload()
                    if user['role'] == 'admin':
                        if 'provider_id' in data:
                            provider_id = data['provider_id']
                            if provider_id is not None and not db.execute("SELECT id FROM users WHERE id=? AND role='provider'", (provider_id,)).fetchone():
                                return self.respond(400, {'error': 'Ungültiger Dienstleister.'})
                            db.execute('UPDATE jobs SET provider_id=?,status=? WHERE id=?', (provider_id, 'assigned' if provider_id else 'open', job_id))
                        if 'status' in data:
                            if data['status'] not in STATUSES:
                                return self.respond(400, {'error': 'Ungültiger Status.'})
                            db.execute('UPDATE jobs SET status=? WHERE id=?', (data['status'], job_id))
                    elif user['role'] == 'provider' and job['provider_id'] == user['id']:
                        if data.get('status') not in ('assigned', 'in_progress', 'done'):
                            return self.respond(400, {'error': 'Ungültiger Status.'})
                        db.execute('UPDATE jobs SET status=? WHERE id=?', (data['status'], job_id))
                    else:
                        return self.respond(403, {'error': 'Keine Berechtigung.'})
                    return self.respond(200, {'ok': True})
                return self.respond(404, {'error': 'Nicht gefunden.'})
        except (ValueError, json.JSONDecodeError) as exc:
            return self.respond(400, {'error': str(exc)})

    def static(self, path):
        requested = (DIST / path.lstrip('/')).resolve()
        if not requested.is_relative_to(DIST.resolve()) or not DIST.exists():
            return self.respond(404, {'error': 'Seite nicht gefunden. Bitte zuerst npm run build ausführen.'})
        if not requested.is_file():
            requested = DIST / 'index.html'
        if not requested.is_file():
            return self.respond(404, {'error': 'Seite nicht gefunden.'})
        body = requested.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(requested.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def login_response(self, db, user):
        token = secrets.token_urlsafe(32)
        db.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES (?,?,?)',
                   (hashlib.sha256(token.encode()).hexdigest(), user['id'], (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()))
        return self.respond(200, {'token': token, 'user': public_user(user)})

    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PATCH(self): self.route('PATCH')


if __name__ == '__main__':
    init_db()
    print(f'MACHBAR API: http://{HOST}:{PORT}/api/health')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

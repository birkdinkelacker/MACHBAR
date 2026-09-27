"""MACHBAR API with SQLite and validated photo uploads."""
import base64
import binascii
import io
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DIST = ROOT.parent / 'dist'
DB = Path(os.environ.get('MACHBAR_DB', ROOT / 'machbar.db'))
HOST = os.environ.get('MACHBAR_HOST', '127.0.0.1')
PORT = int(os.environ.get('MACHBAR_PORT', os.environ.get('PORT', '8000')))
STATUSES = {'open', 'assigned', 'in_progress', 'done'}
ADMIN_EMAIL = 'info.machbar@gmx.de'
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
    DB.parent.mkdir(parents=True, exist_ok=True)
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
        CREATE TABLE IF NOT EXISTS job_admin_notes (
            job_id INTEGER PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE,
            note TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id),
            provider_id INTEGER NOT NULL REFERENCES users(id), created_by INTEGER NOT NULL REFERENCES users(id),
            price_cents INTEGER NOT NULL CHECK(price_cents>0), slots_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted','rejected','superseded')),
            selected_slot INTEGER, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, decided_at TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS one_pending_offer ON offers(job_id) WHERE status='pending';
        CREATE UNIQUE INDEX IF NOT EXISTS one_accepted_offer ON offers(job_id) WHERE status='accepted';
        CREATE TABLE IF NOT EXISTS email_outbox (
            id INTEGER PRIMARY KEY, event_key TEXT NOT NULL UNIQUE, recipient TEXT NOT NULL,
            subject TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            error TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        if 'details_json' not in {row['name'] for row in db.execute('PRAGMA table_info(jobs)')}:
            db.execute("ALTER TABLE jobs ADD COLUMN details_json TEXT NOT NULL DEFAULT '{}'")
        if 'phone' not in {row['name'] for row in db.execute('PRAGMA table_info(users)')}:
            db.execute("ALTER TABLE users ADD COLUMN phone TEXT NOT NULL DEFAULT ''")
        if 'contact_phone' not in {row['name'] for row in db.execute('PRAGMA table_info(jobs)')}:
            db.execute("ALTER TABLE jobs ADD COLUMN contact_phone TEXT NOT NULL DEFAULT ''")
        if 'guest_token_hash' not in {row['name'] for row in db.execute('PRAGMA table_info(jobs)')}:
            db.execute("ALTER TABLE jobs ADD COLUMN guest_token_hash TEXT NOT NULL DEFAULT ''")
        admin_email = ADMIN_EMAIL
        admin_password = os.environ.get('MACHBAR_ADMIN_PASSWORD', '')
        db.execute("UPDATE users SET role='customer' WHERE role='admin' AND lower(email)<>?", (ADMIN_EMAIL,))
        db.execute("UPDATE users SET role='admin',email=? WHERE lower(email)=?", (ADMIN_EMAIL, ADMIN_EMAIL))
        if admin_email and admin_password and not db.execute('SELECT id FROM users WHERE email=?', (admin_email,)).fetchone():
            salt = secrets.token_hex(16)
            db.execute('INSERT INTO users(email,name,company,role,salt,password_hash) VALUES (?,?,?,?,?,?)',
                       (admin_email, 'MACHBAR Admin', 'MACHBAR', 'admin', salt, hash_password(admin_password, salt)))


def hash_password(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1).hex()


def public_user(row):
    return {key: row[key] for key in ('id', 'email', 'name', 'company', 'role', 'phone')}


def valid_phone(value):
    return isinstance(value, str) and len(value) <= 40 and bool(re.fullmatch(r'\+?[0-9 ()/.-]+', value)) and 7 <= len(re.sub(r'[^0-9]', '', value)) <= 15


def is_admin(user):
    return bool(user and user['role'] == 'admin' and user['email'].strip().lower() == ADMIN_EMAIL)


def accepted_offer(db, job):
    return db.execute("SELECT id FROM offers WHERE job_id=? AND provider_id=? AND status='accepted'", (job['id'], job['provider_id'])).fetchone() is not None


def owns_job(user, job):
    return bool(user and user['role'] == 'customer' and job['customer_id'] == user['id'])


def public_offer(row, db):
    offer = dict(row)
    offer['slots'] = json.loads(offer.pop('slots_json'))
    provider = db.execute('SELECT name,company FROM users WHERE id=?', (offer['provider_id'],)).fetchone()
    offer['provider_name'] = provider['company'] or provider['name']
    return offer


def hide_contact_text(value, job):
    """Redact known customer contact details even if repeated in free text."""
    if isinstance(value, list):
        return [hide_contact_text(item, job) for item in value]
    if isinstance(value, dict):
        return {key:hide_contact_text(item, job) for key,item in value.items()}
    if not isinstance(value, str):
        return value
    for key in ('contact_email','address','contact_name'):
        private = job.get(key, '').strip()
        if len(private) > 1:
            value = re.sub(r'(?<!\w)' + re.escape(private) + r'(?!\w)', '[nach Annahme verfügbar]', value, flags=re.IGNORECASE)
    digits = re.sub(r'\D', '', job.get('contact_phone', ''))
    variants = {digits} if digits else set()
    if digits.startswith('0049'):
        variants.update({'49' + digits[4:], '0' + digits[4:]})
    elif digits.startswith('49'):
        variants.update({'00' + digits, '0' + digits[2:]})
    elif digits.startswith('0') and not digits.startswith('00'):
        variants.update({'49' + digits[1:], '0049' + digits[1:]})
    for number in sorted(variants, key=len, reverse=True):
        pattern = r'(?<!\w)\+?' + r'[ ()/.-]*'.join(number) + r'(?!\w)'
        value = re.sub(pattern, '[Telefon nach Annahme]', value)
    value = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[E-Mail nach Annahme]', value)
    # Keep dates and times intact when looking for other phone-like text.
    parts = re.split(r'(\b\d{1,2}\.\d{1,2}\.\d{4}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}:\d{2}\b)', value)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r'(?<!\w)(?:\+|00|0)[0-9 ()/.-]{6,}[0-9](?!\w)',
                          lambda m: '[Telefon nach Annahme]' if 7 <= len(re.sub(r'\D', '', m[0])) <= 15 else m[0], parts[i])
    return ''.join(parts)


def public_job(row, db, user=None):
    job = dict(row)
    job.pop('guest_token_hash', None)
    job['offers'] = [public_offer(o, db) for o in db.execute('SELECT * FROM offers WHERE job_id=? ORDER BY id DESC', (job['id'],))]
    job['contact_released'] = accepted_offer(db, job)
    if job['customer_id']:
        customer = db.execute('SELECT phone FROM users WHERE id=?', (job['customer_id'],)).fetchone()
        if customer and customer['phone']:
            job['contact_phone'] = customer['phone']
    job['details'] = json.loads(job.pop('details_json'))
    job['photos'] = [{'id': photo['id'], 'name': photo['name'], 'url': f"/api/jobs/{job['id']}/photos/{photo['id']}"}
                     for photo in db.execute('SELECT id,name FROM job_photos WHERE job_id=? ORDER BY id', (job['id'],))]
    if user and user['role'] == 'provider' and not job['contact_released']:
        for field in ('title','description','category','city','details'):
            job[field] = hide_contact_text(job[field], job)
        job['region'] = f"{job['city']} · PLZ-Gebiet {job['postal_code'][:2]}***"
        job['offers'] = [o for o in job['offers'] if o['provider_id']==user['id']]
        for i, photo in enumerate(job['photos'], 1):
            photo['name'] = f'Foto {i}'
        for field in ('contact_name','contact_email','contact_phone','address','customer_id','postal_code'):
            job.pop(field, None)
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
    if not isinstance(work, list) or len(work) > 100 or any(not isinstance(item, str) or len(item) > 150 for item in work):
        raise ValueError('Ungültige Auswahl der Arbeiten.')
    result['work'] = work
    if 'services' in value:
        services = value['services']
        if not isinstance(services, list) or not 1 <= len(services) <= 100 or any(not isinstance(item, str) or not item.strip() or len(item) > 150 for item in services):
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
    slots = value.get('availability', [])
    days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    if not isinstance(slots, list) or len(slots) > 7:
        raise ValueError('Bitte höchstens sieben Wochentage angeben.')
    if 'availability' in value:
        result['availability'] = []
    seen = set()
    for slot in slots:
        if not isinstance(slot, dict) or not isinstance(slot.get('day'), str) or slot['day'] not in days or slot['day'] in seen:
            raise ValueError('Ungültige oder doppelte Wochentage.')
        start, end = slot.get('from'), slot.get('to')
        if any(not isinstance(t, str) or not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', t) for t in (start, end)) or start >= end:
            raise ValueError('Bitte gültige Zeitfenster angeben: Ende nach Beginn.')
        seen.add(slot['day'])
        result['availability'].append({'day': slot['day'], 'from': start, 'to': end})
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


def can_view_job(user, job, db):
    return user and (is_admin(user) or
        (user['role'] == 'provider' and job['provider_id'] == user['id']) or owns_job(user, job))


def offer_input(data):
    price = str(data.get('price', '')).replace(',', '.')
    if not re.fullmatch(r'\d{1,7}(\.\d{1,2})?', price) or not Decimal('0') < Decimal(price) <= Decimal('1000000'):
        raise ValueError('Bitte einen geschätzten Gesamtpreis zwischen 0,01 und 1.000.000 Euro angeben.')
    slots = data.get('slots')
    if not isinstance(slots, list) or not 1 <= len(slots) <= 5:
        raise ValueError('Bitte ein bis fünf Terminvorschläge angeben.')
    clean = []
    today = datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat()
    for slot in slots:
        if not isinstance(slot, dict):
            raise ValueError('Ungültiger Terminvorschlag.')
        date, start, end = slot.get('date'), slot.get('from'), slot.get('to')
        try:
            if not isinstance(date, str) or datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d') != date or date < today:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError('Bitte heutige oder zukünftige Termine wählen.') from None
        if any(not isinstance(t, str) or not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', t) for t in (start, end)) or start >= end:
            raise ValueError('Bitte gültige Start- und Endzeiten angeben.')
        item = {'date':date,'from':start,'to':end}
        if item in clean:
            raise ValueError('Bitte unterschiedliche Termine angeben.')
        clean.append(item)
    return int(Decimal(price)*100), clean


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

    def guest_owns(self, job):
        token = self.headers.get('X-Guest-Token', '')
        return bool(job and job['customer_id'] is None and token and job['guest_token_hash'] and hmac.compare_digest(job['guest_token_hash'], hashlib.sha256(token.encode()).hexdigest()))

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
                    phone = data.get('phone', '')
                    phone = phone.strip() if isinstance(phone, str) else phone
                    if email == ADMIN_EMAIL:
                        return self.respond(403, {'error': 'Dieses Konto ist für die Administration reserviert. Bitte anmelden oder die lokale Admin-Ersteinrichtung verwenden.'})
                    if not email or '@' not in email or len(email) > 254 or not name or len(name) > 100 or len(password) < 8 or role not in ('customer', 'provider'):
                        return self.respond(400, {'error': 'Bitte gültige Angaben und ein Passwort mit mindestens 8 Zeichen eingeben.'})
                    if not valid_phone(phone):
                        return self.respond(400, {'error': 'Bitte eine gültige Telefonnummer mit 7 bis 15 Ziffern angeben.'})
                    salt = secrets.token_hex(16)
                    try:
                        cur = db.execute('INSERT INTO users(email,name,company,role,salt,password_hash,phone) VALUES (?,?,?,?,?,?,?)',
                                         (email, name, str(data.get('company', ''))[:120], role, salt, hash_password(password, salt), phone))
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
                if method == 'PATCH' and path == '/api/auth/settings':
                    if not user:
                        return self.respond(401, {'error':'Bitte anmelden.'})
                    if is_admin(user) or user['role'] not in ('customer','provider'):
                        return self.respond(403, {'error':'Dieses Konto kann die Rolle nicht wechseln.'})
                    data = self.payload()
                    role = data.get('role', user['role'])
                    if set(data) - {'role'} or role not in ('customer','provider'):
                        return self.respond(400, {'error':'Hier kann nur die aktive Kunden- oder Dienstleisterrolle geändert werden.'})
                    db.execute('UPDATE users SET role=? WHERE id=?', (role, user['id']))
                    return self.respond(200, {'user':public_user(db.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone())})
                if method == 'GET' and path == '/api/admin/dashboard':
                    if not is_admin(user):
                        return self.respond(403, {'error': 'Kein Zugriff auf die Administration.'})
                    notes = {row['job_id']: row['note'] for row in db.execute('SELECT * FROM job_admin_notes')}
                    jobs = [{**public_job(row, db), 'admin_note': notes.get(row['id'], '')}
                            for row in db.execute('SELECT * FROM jobs ORDER BY id DESC').fetchall()]
                    providers = [public_user(row) for row in db.execute("SELECT * FROM users WHERE role='provider' ORDER BY company,name")]
                    customers = db.execute("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0]
                    return self.respond(200, {'jobs': jobs, 'providers': providers, 'customers': customers,
                                             'updated_at': datetime.now(timezone.utc).isoformat()})
                if method == 'GET' and path == '/api/providers':
                    if not is_admin(user):
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
                    contact_phone = user['phone'] if user else str(data.get('contact_phone', '')).strip()
                    if contact_phone and not valid_phone(contact_phone):
                        return self.respond(400, {'error':'Bitte eine gültige Telefonnummer angeben.'})
                    if not category or not title or len(description) < 15 or len(postal_code) != 5 or not postal_code.isdigit() or not city or not contact_name or '@' not in contact_email:
                        return self.respond(400, {'error': 'Bitte alle Pflichtfelder korrekt ausfüllen.'})
                    details_json = request_details(data.get('details', {}))
                    slots = json.loads(details_json).get('availability', [])
                    if slots and data.get('desired_date'):
                        try:
                            desired_day = datetime.strptime(data['desired_date'], '%Y-%m-%d').weekday()
                        except (ValueError, TypeError):
                            raise ValueError('Ungültiger Wunschtermin.') from None
                        if not any(slot['day'] == ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'][desired_day] for slot in slots):
                            raise ValueError('Wunschtermin und verfügbare Wochentage passen nicht zusammen.')
                    photos = prepare_photos(data.get('photos', []))
                    cur = db.execute('''INSERT INTO jobs(customer_id,category,title,description,postal_code,city,address,desired_date,contact_name,contact_email,details_json,contact_phone)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (user['id'] if user else None, category, title, description, postal_code, city,
                        str(data.get('address', '')).strip()[:200], str(data.get('desired_date', '')).strip()[:20], contact_name, contact_email, details_json, contact_phone))
                    guest_token = secrets.token_urlsafe(32) if not user else ''
                    if guest_token:
                        db.execute('UPDATE jobs SET guest_token_hash=? WHERE id=?',(hashlib.sha256(guest_token.encode()).hexdigest(),cur.lastrowid))
                    db.executemany('INSERT INTO job_photos(job_id,name,mime,data) VALUES (?,?,?,?)',
                                   [(cur.lastrowid, name, mime, photo_data) for name, mime, photo_data in photos])
                    db.commit()
                    return self.respond(201, {'id': cur.lastrowid, 'message': 'Anfrage eingegangen.', 'guest_token':guest_token})
                match = re.fullmatch(r'/api/jobs/(\d+)/offers', path)
                if method == 'POST' and match:
                    if not user:
                        return self.respond(401, {'error':'Bitte anmelden.'})
                    data = self.payload()
                    price, slots = offer_input(data)
                    db.execute('BEGIN IMMEDIATE')
                    job = db.execute('SELECT * FROM jobs WHERE id=?',(int(match[1]),)).fetchone()
                    if not job or not (is_admin(user) or (user['role']=='provider' and job['provider_id']==user['id'] and job['customer_id']!=user['id'])):
                        return self.respond(403, {'error':'Keine Berechtigung für dieses Angebot.'})
                    if 'admin_note' in data:
                        if not is_admin(user):
                            return self.respond(403, {'error':'Interne Notizen dürfen nur von der Administration bearbeitet werden.'})
                        if not isinstance(data['admin_note'], str) or len(data['admin_note']) > 5000:
                            return self.respond(400, {'error':'Interne Notizen dürfen höchstens 5.000 Zeichen enthalten.'})
                    if job['status'] in ('in_progress','done') or accepted_offer(db, job):
                        return self.respond(409, {'error':'Der Auftrag wurde bereits angenommen oder abgeschlossen.'})
                    provider_id = data.get('provider_id',job['provider_id']) if is_admin(user) else user['id']
                    if type(provider_id) is not int or provider_id==job['customer_id'] or not db.execute("SELECT id FROM users WHERE id=? AND role='provider'",(provider_id,)).fetchone():
                        return self.respond(400, {'error':'Bitte einen Dienstleister auswählen.'})
                    db.execute("UPDATE offers SET status='superseded' WHERE job_id=? AND status='pending'",(job['id'],))
                    db.execute("UPDATE jobs SET provider_id=?,status='assigned' WHERE id=?",(provider_id,job['id']))
                    offer = db.execute('INSERT INTO offers(job_id,provider_id,created_by,price_cents,slots_json) VALUES(?,?,?,?,?)',(job['id'],provider_id,user['id'],price,json.dumps(slots)))
                    if 'admin_note' in data:
                        db.execute('INSERT INTO job_admin_notes(job_id,note) VALUES (?,?) ON CONFLICT(job_id) DO UPDATE SET note=excluded.note', (job['id'],data['admin_note'].strip()))
                    db.commit()
                    return self.respond(201, {'id':offer.lastrowid})
                match = re.fullmatch(r'/api/offers/(\d+)/decision', path)
                if method == 'POST' and match:
                    data = self.payload()
                    db.execute('BEGIN IMMEDIATE')
                    offer = db.execute('SELECT * FROM offers WHERE id=?',(int(match[1]),)).fetchone()
                    job = db.execute('SELECT * FROM jobs WHERE id=?',(offer['job_id'],)).fetchone() if offer else None
                    if not job or not (owns_job(user,job) or self.guest_owns(job)):
                        return self.respond(403, {'error':'Nur der Kunde kann dieses Angebot beantworten.'})
                    if offer['status']!='pending' or job['provider_id']!=offer['provider_id']:
                        return self.respond(409, {'error':'Dieses Angebot ist nicht mehr offen. Bitte aktualisieren.'})
                    decision, selected = data.get('decision'), data.get('selected_slot')
                    if decision not in ('accepted','rejected'):
                        return self.respond(400, {'error':'Bitte annehmen oder ablehnen wählen.'})
                    if decision=='accepted':
                        slots = json.loads(offer['slots_json'])
                        if type(selected) is not int or not 0 <= selected < len(slots):
                            return self.respond(400, {'error':'Bitte einen vorgeschlagenen Termin auswählen.'})
                        chosen = slots[selected]
                        if datetime.fromisoformat(chosen['date']+'T'+chosen['from']).replace(tzinfo=ZoneInfo('Europe/Berlin')) <= datetime.now(ZoneInfo('Europe/Berlin')):
                            return self.respond(409, {'error':'Dieser Termin ist bereits verstrichen. Bitte einen neuen Vorschlag anfordern.'})
                    else:
                        selected = None
                    db.execute('UPDATE offers SET status=?,selected_slot=?,decided_at=? WHERE id=?',(decision,selected,datetime.now(timezone.utc).isoformat(),offer['id']))
                    db.commit()
                    return self.respond(200, {'ok':True})
                match = re.fullmatch(r'/api/jobs/(\d+)', path)
                if method == 'DELETE' and match:
                    if not is_admin(user):
                        return self.respond(403, {'error':'Nur die Administration kann Aufträge löschen.'})
                    job_id = int(match[1])
                    db.execute('BEGIN IMMEDIATE')
                    if not db.execute('SELECT id FROM jobs WHERE id=?',(job_id,)).fetchone():
                        return self.respond(404, {'error':'Auftrag nicht gefunden.'})
                    offer_ids = [row['id'] for row in db.execute('SELECT id FROM offers WHERE job_id=?',(job_id,))]
                    # Remove old, disabled outbox entries associated with this job as well.
                    for offer_id in offer_ids:
                        db.execute("DELETE FROM email_outbox WHERE event_key=? OR event_key LIKE ?",(f'offer-{offer_id}',f'decision-{offer_id}-%'))
                    db.execute('DELETE FROM email_outbox WHERE event_key=?',(f'guest-{job_id}',))
                    db.execute('DELETE FROM offers WHERE job_id=?',(job_id,))
                    db.execute('DELETE FROM jobs WHERE id=?',(job_id,))
                    return self.respond(200, {'ok':True})
                if method == 'GET' and match:
                    job = db.execute('SELECT * FROM jobs WHERE id=?',(int(match[1]),)).fetchone()
                    if not job or not (is_admin(user) or owns_job(user,job) or self.guest_owns(job) or (user and user['role']=='provider' and job['provider_id']==user['id'])):
                        return self.respond(403, {'error':'Kein Zugriff auf diesen Auftrag.'})
                    return self.respond(200, {'job':public_job(job,db,user if not self.guest_owns(job) else None)})
                if method == 'GET' and path.startswith('/api/jobs/') and '/photos/' in path:
                    parts = path.split('/')
                    if len(parts) != 6 or not parts[3].isdigit() or not parts[5].isdigit():
                        return self.respond(404, {'error': 'Foto nicht gefunden.'})
                    job = db.execute('SELECT * FROM jobs WHERE id=?', (int(parts[3]),)).fetchone()
                    if not user and not self.guest_owns(job):
                        return self.respond(401, {'error': 'Bitte anmelden.'})
                    if not job or not (can_view_job(user, job, db) or self.guest_owns(job)):
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
                    if is_admin(user):
                        rows = db.execute('SELECT * FROM jobs ORDER BY id DESC').fetchall()
                    elif user['role'] == 'admin':
                        return self.respond(403, {'error': 'Keine Berechtigung.'})
                    elif user['role'] == 'provider':
                        rows = db.execute('SELECT * FROM jobs WHERE provider_id=? ORDER BY id DESC', (user['id'],)).fetchall()
                    else:
                        rows = db.execute('SELECT * FROM jobs WHERE customer_id=? ORDER BY id DESC', (user['id'],)).fetchall()
                    return self.respond(200, {'jobs': [public_job(row, db, user) for row in rows]})
                if method == 'PATCH' and path.startswith('/api/jobs/'):
                    if not user:
                        return self.respond(401, {'error': 'Bitte anmelden.'})
                    try:
                        job_id = int(path.split('/')[-1])
                    except ValueError:
                        return self.respond(404, {'error': 'Auftrag nicht gefunden.'})
                    db.execute('BEGIN IMMEDIATE')
                    job = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
                    if not job:
                        return self.respond(404, {'error': 'Auftrag nicht gefunden.'})
                    data = self.payload()
                    if is_admin(user):
                        if 'status' in data and (not isinstance(data['status'], str) or data['status'] not in STATUSES):
                            return self.respond(400, {'error': 'Ungültiger Status.'})
                        if 'admin_note' in data and (not isinstance(data['admin_note'], str) or len(data['admin_note']) > 5000):
                            return self.respond(400, {'error': 'Interne Notizen dürfen höchstens 5.000 Zeichen enthalten.'})
                        if 'provider_id' in data:
                            provider_id = data['provider_id']
                            if provider_id is not None and provider_id == job['customer_id']:
                                return self.respond(400, {'error':'Kunden können ihren eigenen Auftrag nicht übernehmen.'})
                            if provider_id != job['provider_id'] and accepted_offer(db, job):
                                return self.respond(409, {'error':'Der Kunde hat diesen Dienstleister bereits bestätigt. Keine Neuzuweisung möglich.'})
                            if provider_id is not None and (type(provider_id) is not int or not db.execute("SELECT id FROM users WHERE id=? AND role='provider'", (provider_id,)).fetchone()):
                                return self.respond(400, {'error': 'Ungültiger Dienstleister.'})
                            next_status = data.get('status', job['status'] if job['status'] in ('in_progress', 'done') else 'assigned' if provider_id else 'open')
                            if provider_id != job['provider_id']:
                                db.execute("UPDATE offers SET status='superseded' WHERE job_id=? AND status='pending'",(job_id,))
                            db.execute('UPDATE jobs SET provider_id=?,status=? WHERE id=?', (provider_id, next_status, job_id))
                        if 'status' in data:
                            if data['status'] not in STATUSES:
                                return self.respond(400, {'error': 'Ungültiger Status.'})
                            db.execute('UPDATE jobs SET status=? WHERE id=?', (data['status'], job_id))
                        if 'admin_note' in data:
                            db.execute('INSERT INTO job_admin_notes(job_id,note) VALUES (?,?) ON CONFLICT(job_id) DO UPDATE SET note=excluded.note', (job_id, data['admin_note'].strip()))
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
    def do_DELETE(self): self.route('DELETE')


if __name__ == '__main__':
    init_db()
    print(f'MACHBAR API: http://{HOST}:{PORT}/api/health')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

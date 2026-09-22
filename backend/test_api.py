import json
import base64
import io
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PIL import Image

try:
    from . import server
except ImportError:
    import server


class APITest(unittest.TestCase):
    def setUp(self):
        server.DB = server.ROOT / 'test_api.db'
        server.DB.unlink(missing_ok=True)
        os.environ['MACHBAR_ADMIN_EMAIL'] = 'admin@example.com'
        os.environ['MACHBAR_ADMIN_PASSWORD'] = 'admin-password-123'
        server.init_db()
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.httpd.server_port}'

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        server.DB.unlink(missing_ok=True)

    def call(self, path, method='GET', body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        req = Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                      headers=headers, method=method)
        try:
            with urlopen(req) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            try:
                return error.code, json.load(error)
            finally:
                error.close()

    def test_registration_request_and_role_permissions(self):
        _, customer = self.call('/api/auth/register', 'POST', {'name': 'Kunde', 'email': 'kunde@example.com', 'password': 'password123', 'role': 'customer'})
        _, provider = self.call('/api/auth/register', 'POST', {'name': 'Partner', 'email': 'partner@example.com', 'password': 'password123', 'role': 'provider'})
        _, admin = self.call('/api/auth/login', 'POST', {'email': 'admin@example.com', 'password': 'admin-password-123'})
        self.assertEqual(self.call('/api/auth/register', 'POST', {'name': 'Fake', 'email': 'fake@example.com', 'password': 'password123', 'role': 'admin'})[0], 400)
        status, job = self.call('/api/jobs', 'POST', {'category': 'Entrümpelung', 'title': 'Wohnung räumen', 'description': 'Bitte die gesamte Wohnung räumen.', 'postal_code': '69412', 'city': 'Eberbach'}, customer['token'])
        self.assertEqual(status, 201)
        self.assertEqual(len(self.call('/api/jobs', token=customer['token'])[1]['jobs']), 1)
        self.assertEqual(len(self.call('/api/jobs', token=provider['token'])[1]['jobs']), 0)
        self.assertEqual(self.call(f"/api/jobs/{job['id']}", 'PATCH', {'status': 'done'}, provider['token'])[0], 403)
        self.assertEqual(self.call(f"/api/jobs/{job['id']}", 'PATCH', {'provider_id': provider['user']['id']}, admin['token'])[0], 200)
        self.assertEqual(len(self.call('/api/jobs', token=provider['token'])[1]['jobs']), 1)
        self.assertEqual(self.call(f"/api/jobs/{job['id']}", 'PATCH', {'status': 'done'}, provider['token'])[0], 200)
        self.assertEqual(self.call('/api/jobs', token=customer['token'])[1]['jobs'][0]['status'], 'done')

    def test_wizard_details_persist_and_invalid_details_are_rejected(self):
        body = {'category': 'Umzug', 'title': 'Umzug: Kompletter Umzug',
                'description': 'Arbeiten: Kompletter Umzug\nUmzugsziel: 69115 Heidelberg',
                'postal_code': '69412', 'city': 'Eberbach', 'contact_name': 'Gast', 'contact_email': 'gast@example.com',
                'details': {'work': ['Kompletter Umzug'], 'amount': '60 m²', 'detail_label': 'Zugang',
                            'detail': 'Über Treppen', 'timing': 'Ich bin flexibel', 'destination': '69115 Heidelberg', 'notes': ''}}
        status, job = self.call('/api/jobs', 'POST', body)
        self.assertEqual(status, 201)
        server.init_db()  # Repeated startup preserves existing requests and their answers.
        _, admin = self.call('/api/auth/login', 'POST', {'email': 'admin@example.com', 'password': 'admin-password-123'})
        saved = self.call('/api/jobs', token=admin['token'])[1]['jobs'][0]
        self.assertEqual(saved['id'], job['id'])
        self.assertEqual(saved['details'], body['details'])
        self.assertEqual(saved['description'], body['description'])
        for invalid in [[], {'work': 'invalid'}, {'notes': 'x' * 2001}, {'work': [None]}]:
            self.assertEqual(self.call('/api/jobs', 'POST', {**body, 'details': invalid})[0], 400)

    def test_multiple_services_photos_and_access_control(self):
        def register(name, role='customer'):
            return self.call('/api/auth/register', 'POST', {'name': name, 'email': name+'@example.com', 'password': 'test-password-123', 'role': role})[1]
        owner, other, provider = register('owner'), register('other'), register('provider', 'provider')
        admin = self.call('/api/auth/login', 'POST', {'email': 'admin@example.com', 'password': 'admin-password-123'})[1]
        photo_buffer = io.BytesIO()
        Image.new('RGB', (20, 20), 'red').save(photo_buffer, format='PNG')
        photo = {'name': 'auftrag.png', 'data': 'data:image/png;base64,'+base64.b64encode(photo_buffer.getvalue()).decode()}
        services = ['Wohnung entrümpeln', 'Fensterreinigung', 'Wände und Decken streichen']
        details = {'services': services, 'work': services, 'scopes': [{'group': 'Reinigung', 'amount': '20 m²', 'detail_label': 'Häufigkeit', 'detail': 'Einmalig'}]}
        body = {'category': 'Mehrere Leistungen', 'title': 'Wohnung vorbereiten', 'description': 'Entrümpelung, Reinigung und Malerarbeiten.', 'postal_code': '69412', 'city': 'Eberbach', 'details': details, 'photos': [photo]}
        status, job = self.call('/api/jobs', 'POST', body, owner['token'])
        self.assertEqual(status, 201)
        saved = self.call('/api/jobs', token=owner['token'])[1]['jobs'][0]
        self.assertEqual(saved['details']['services'], services)
        self.assertEqual(saved['details']['scopes'], details['scopes'])
        self.assertEqual(len(saved['photos']), 1)
        url = saved['photos'][0]['url']
        self.assertEqual(self.call(url)[0], 401)
        self.assertEqual(self.call(url, token=other['token'])[0], 403)
        self.assertEqual(self.call(url, token=provider['token'])[0], 403)
        self.call(f"/api/jobs/{job['id']}", 'PATCH', {'provider_id': provider['user']['id']}, admin['token'])
        for account in [owner, provider, admin]:
            with urlopen(Request(self.base+url, headers={'Authorization': 'Bearer '+account['token']})) as response:
                self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
                with Image.open(io.BytesIO(response.read())) as image:
                    self.assertEqual(image.size, (20, 20))
                    self.assertEqual(len(image.getexif()), 0)
        # A bad photo rejects the whole request, even after an earlier valid photo.
        for photos in [[photo]*7, [photo, {**photo, 'data': 'data:image/png;base64,bm90YW5pbWFnZQ=='}], [{**photo, 'data': 'data:image/svg+xml;base64,PHN2Zz4='}]]:
            self.assertEqual(self.call('/api/jobs', 'POST', {**body, 'photos': photos}, owner['token'])[0], 400)
        self.assertEqual(len(self.call('/api/jobs', token=owner['token'])[1]['jobs']), 1)
        with server.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM job_photos').fetchone()[0], 1)

    def test_photo_byte_limit(self):
        with self.assertRaises(ValueError):
            server.prepare_photos([{'name': 'large.png', 'data': 'data:image/png;base64,'+base64.b64encode(b'x'*(server.MAX_PHOTO_BYTES+1)).decode()}])


if __name__ == '__main__':
    unittest.main()

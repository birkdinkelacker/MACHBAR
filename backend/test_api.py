import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

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


if __name__ == '__main__':
    unittest.main()

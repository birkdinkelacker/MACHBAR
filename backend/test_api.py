import json
import base64
import io
import os
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PIL import Image

try:
    from . import server
except ImportError:
    import server


class APITest(unittest.TestCase):
    def account(self, name, role='customer'):
        status, data = self.call('/api/auth/register','POST',{'name':name,'email':name+'@example.com','phone':'+49 162 1234567','password':'test-password-123','role':role})
        self.assertEqual(status,200)
        return data

    def admin(self):
        return self.call('/api/auth/login','POST',{'email':server.ADMIN_EMAIL,'password':'admin-password-123'})[1]

    def offer_body(self):
        return {'price':'250,50','slots':[{'date':'2099-10-05','from':'09:00','to':'12:00'},{'date':'2099-10-06','from':'14:00','to':'16:00'}]}

    def accept_offer(self, job_id, provider, owner):
        status, offer = self.call(f'/api/jobs/{job_id}/offers','POST',self.offer_body(),provider['token'])
        self.assertEqual(status,201)
        self.assertEqual(self.call(f"/api/offers/{offer['id']}/decision",'POST',{'decision':'accepted','selected_slot':0},owner['token'])[0],200)

    def test_offer_acceptance_releases_only_assigned_provider_and_prevents_stale_actions(self):
        owner,provider,other = self.account('owner'),self.account('provider','provider'),self.account('other','provider')
        admin = self.admin()
        job = self.call('/api/jobs','POST',{'category':'Elektrik','title':'Leuchten für owner anschließen','description':'Zwei Leuchten am 05.10.2099 von 09:00 bis 12:00 montieren. Kontakt: owner@example.com, 0162/1234567, SecretStreet 3.','address':'SecretStreet 3','postal_code':'69412','city':'Eberbach','desired_date':'2099-10-05','details':{'services':['Leuchten anschließen'],'notes':'Leiter ist vorhanden. Rückfrage: +49 (162) 1234567','availability':[{'day':'Montag','from':'09:00','to':'12:00'}]}},owner['token'])[1]
        path = f"/api/jobs/{job['id']}"
        self.call(path,'PATCH',{'provider_id':provider['user']['id']},admin['token'])
        before = self.call('/api/jobs',token=provider['token'])[1]['jobs'][0]
        self.assertEqual(before['region'],'Eberbach · PLZ-Gebiet 69***')
        for field in ('contact_name','contact_email','contact_phone','address','postal_code','customer_id'):
            self.assertNotIn(field,before)
        for private in ('owner', 'example.com', '1234567', 'SecretStreet', '69412'):
            self.assertNotIn(private,json.dumps(before))
        self.assertIn('Leuchten', before['title'])
        self.assertIn('Zwei Leuchten am 05.10.2099 von 09:00 bis 12:00 montieren.',before['description'])
        self.assertEqual(before['desired_date'],'2099-10-05')
        self.assertEqual(before['details']['services'],['Leuchten anschließen'])
        self.assertEqual(before['details']['availability'],[{'day':'Montag','from':'09:00','to':'12:00'}])
        self.assertIn('Leiter ist vorhanden.',before['details']['notes'])
        self.assertEqual(self.call(path,token=other['token'])[0],403)
        self.assertEqual(self.call(path+'/offers','POST',self.offer_body(),other['token'])[0],403)
        self.assertEqual(self.call(path+'/offers','POST',{**self.offer_body(),'price':'NaN'},provider['token'])[0],400)
        first = self.call(path+'/offers','POST',self.offer_body(),provider['token'])[1]
        second = self.call(path+'/offers','POST',self.offer_body(),provider['token'])[1]
        def decide(oid,who,decision='accepted',slot=1):
            return self.call(f'/api/offers/{oid}/decision','POST',{'decision':decision,'selected_slot':slot},who['token'])[0]
        self.assertEqual(decide(first['id'],owner),409)
        self.assertEqual(decide(second['id'],other),403)
        self.assertEqual(decide(second['id'],admin),403)
        self.assertEqual(decide(second['id'],owner,slot=99),400)
        self.assertEqual(decide(second['id'],owner),200)
        self.assertEqual(decide(second['id'],owner,'rejected'),409)
        after = self.call(path,token=provider['token'])[1]['job']
        self.assertTrue(after['contact_released']); self.assertEqual(after['contact_phone'],'+49 162 1234567')
        self.assertEqual(after['address'],'SecretStreet 3')
        self.assertEqual(after['offers'][0]['price_cents'],25050)
        self.assertEqual(after['offers'][0]['selected_slot'],1)
        self.assertEqual(self.call(path,'PATCH',{'provider_id':other['user']['id']},admin['token'])[0],409)
        self.assertEqual(self.call(path+'/offers','POST',self.offer_body(),provider['token'])[0],409)
        with server.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM email_outbox').fetchone()[0],0)

    def test_admin_saves_assignment_note_and_offer_together(self):
        admin, owner = self.admin(), self.account('owner')
        provider, other = self.account('provider','provider'), self.account('other','provider')
        job = self.call('/api/jobs','POST',{'category':'Montage','title':'Regal montieren','description':'Ein Regal an der Wand befestigen.','postal_code':'69412','city':'Eberbach'},owner['token'])[1]
        path = f"/api/jobs/{job['id']}"
        self.assertEqual(self.call(path,'PATCH',{'provider_id':provider['user']['id'],'admin_note':'Bisherige Notiz'},admin['token'])[0],200)
        old_offer = self.call(path+'/offers','POST',self.offer_body(),provider['token'])[1]
        body = {**self.offer_body(),'provider_id':other['user']['id'],'admin_note':' Neue interne Abstimmung '}
        for invalid in ({**body,'price':'0'},{**body,'admin_note':'x'*5001},{**body,'slots':[]}):
            self.assertEqual(self.call(path+'/offers','POST',invalid,admin['token'])[0],400)
            saved = self.call('/api/admin/dashboard',token=admin['token'])[1]['jobs'][0]
            self.assertEqual(saved['provider_id'],provider['user']['id'])
            self.assertEqual(saved['admin_note'],'Bisherige Notiz')
            self.assertEqual([(o['id'],o['status']) for o in saved['offers']],[(old_offer['id'],'pending')])
        self.assertEqual(self.call(path+'/offers','POST',{**self.offer_body(),'admin_note':'Unerlaubt'},provider['token'])[0],403)
        self.assertEqual(self.call(path+'/offers','POST',body,admin['token'])[0],201)
        saved = self.call('/api/admin/dashboard',token=admin['token'])[1]['jobs'][0]
        self.assertEqual(saved['provider_id'],other['user']['id'])
        self.assertEqual(saved['status'],'assigned')
        self.assertEqual(saved['admin_note'],'Neue interne Abstimmung')
        self.assertEqual([o['status'] for o in saved['offers']],['pending','superseded'])
        self.assertEqual(saved['offers'][0]['price_cents'],25050)
        for account in (owner,other):
            self.assertNotIn('admin_note',self.call(path,token=account['token'])[1]['job'])

    def test_guest_link_and_rejection_do_not_expose_contact_or_allow_email_impersonation(self):
        admin,provider = self.admin(),self.account('provider','provider')
        job = self.call('/api/jobs','POST',{'category':'Reinigung','title':'Fenster','description':'Fenster gründlich reinigen','postal_code':'69412','city':'Eberbach','contact_name':'Gast','contact_email':'guest@example.com','contact_phone':'06271 123456'})[1]
        path = f"/api/jobs/{job['id']}"
        impostor = self.account('guest')
        self.assertEqual(self.call('/api/jobs',token=impostor['token'])[1]['jobs'],[])
        self.assertEqual(self.call(path,token=impostor['token'])[0],403)
        self.assertEqual(self.call(path,guest='wrong')[0],403)
        self.assertEqual(self.call(path,guest=job['guest_token'])[0],200)
        offer = self.call(path+'/offers','POST',{**self.offer_body(),'provider_id':provider['user']['id']},admin['token'])[1]
        decision = f"/api/offers/{offer['id']}/decision"
        self.assertEqual(self.call(decision,'POST',{'decision':'accepted','selected_slot':0},impostor['token'])[0],403)
        self.assertEqual(self.call(decision,'POST',{'decision':'rejected'},guest=job['guest_token'])[0],200)
        self.assertFalse(self.call(path,token=provider['token'])[1]['job']['contact_released'])
        with server.connect() as db:
            stored = db.execute('SELECT guest_token_hash FROM jobs WHERE id=?',(job['id'],)).fetchone()[0]
            self.assertNotEqual(stored,job['guest_token'])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM email_outbox').fetchone()[0],0)

    def test_settings_role_switch_preserves_work_and_cannot_grant_admin_or_self_assign(self):
        customer,admin = self.account('switch'),self.admin()
        token = customer['token']
        job=self.call('/api/jobs','POST',{'category':'Reinigung','title':'Fenster','description':'Fenster gründlich reinigen','postal_code':'69412','city':'Eberbach'},token)[1]
        self.assertEqual(self.call('/api/auth/settings','PATCH',{'role':'admin'},token)[0],400)
        self.assertEqual(self.call('/api/auth/settings','PATCH',{'role':'provider','phone':'06271 654321'},token)[0],400)
        self.assertEqual(self.call('/api/auth/settings','PATCH',{'role':'provider'},token)[0],200)
        self.assertEqual(self.call('/api/auth/me',token=token)[1]['user']['role'],'provider')
        self.assertEqual(self.call('/api/auth/me',token=token)[1]['user']['phone'],'+49 162 1234567')
        self.assertEqual(self.call('/api/jobs',token=token)[1]['jobs'],[])
        self.assertEqual(self.call(f"/api/jobs/{job['id']}",'PATCH',{'provider_id':customer['user']['id']},admin['token'])[0],400)
        self.assertEqual(self.call('/api/auth/settings','PATCH',{'role':'customer'},token)[0],200)
        self.assertEqual(len(self.call('/api/jobs',token=token)[1]['jobs']),1)
        self.assertEqual(self.call('/api/auth/settings','PATCH',{'role':'provider'},admin['token'])[0],403)

    def test_phone_and_availability_persist_and_are_validated(self):
        account = {'name': 'Telefon-Test', 'email': 'phone@example.com', 'password': 'test-password-123', 'role': 'customer'}
        for phone in (None, '', 'abc12345678', '123', '+49 1234567890123456789'):
            self.assertEqual(self.call('/api/auth/register', 'POST', {**account, 'phone': phone})[0], 400)
        status, customer = self.call('/api/auth/register', 'POST', {**account, 'phone': '+49 (162) 1234567'})
        self.assertEqual(status, 200)
        self.assertEqual(customer['user']['phone'], '+49 (162) 1234567')
        token = customer['token']
        server.init_db()  # Schema upgrades are repeatable and preserve accounts.
        self.assertEqual(self.call('/api/auth/me', token=token)[1]['user']['phone'], '+49 (162) 1234567')
        slots = [{'day': 'Montag', 'from': '09:00', 'to': '12:30'}]
        job = {'category': 'Elektrik', 'title': 'Leuchten anschließen', 'description': 'Bitte zwei Leuchten fachgerecht anschließen.', 'postal_code': '69412', 'city': 'Eberbach', 'desired_date': '2026-09-28', 'details': {'availability': slots}}
        self.assertEqual(self.call('/api/jobs', 'POST', job, token)[0], 201)
        saved = self.call('/api/jobs', token=token)[1]['jobs'][0]
        self.assertEqual(saved['details']['availability'], slots)
        self.assertEqual(saved['contact_phone'], '+49 (162) 1234567')
        for invalid in ([{'day': 'Montag', 'from': '12:00', 'to': '09:00'}], slots * 2, [{'day': 'Montag', 'from': '24:00', 'to': '25:00'}]):
            self.assertEqual(self.call('/api/jobs', 'POST', {**job, 'details': {'availability': invalid}}, token)[0], 400)
        self.assertEqual(self.call('/api/jobs', 'POST', {**job, 'desired_date': '2026-09-29'}, token)[0], 400)
        self.assertEqual(len(self.call('/api/jobs', token=token)[1]['jobs']), 1)

    def setUp(self):
        # Even old, complete SMTP settings cannot activate mail delivery.
        env = patch.dict(os.environ, {'MACHBAR_SMTP_HOST':'smtp.example.com','MACHBAR_SMTP_PORT':'465',
            'MACHBAR_SMTP_USER':'test-only','MACHBAR_SMTP_PASSWORD':'test-only',
            'MACHBAR_MAIL_FROM':'info.machbar@gmx.de','MACHBAR_PUBLIC_URL':'https://example.com'})
        env.start()
        self.addCleanup(env.stop)
        smtp_patch, ssl_patch = patch('smtplib.SMTP'), patch('smtplib.SMTP_SSL')
        self.smtp, self.smtp_ssl = smtp_patch.start(), ssl_patch.start()
        self.addCleanup(smtp_patch.stop)
        self.addCleanup(ssl_patch.stop)
        server.DB = server.ROOT / 'test_api.db'
        server.DB.unlink(missing_ok=True)
        os.environ['MACHBAR_ADMIN_EMAIL'] = 'info.machbar@gmx.de'
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
        self.smtp.assert_not_called()
        self.smtp_ssl.assert_not_called()

    def call(self, path, method='GET', body=None, token=None, guest=None):
        headers = {'Content-Type': 'application/json'}
        if guest:
            headers['X-Guest-Token'] = guest
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
        _, customer = self.call('/api/auth/register', 'POST', {'name': 'Kunde', 'email': 'kunde@example.com', 'phone': '+49 162 1234567', 'password': 'password123', 'role': 'customer'})
        _, provider = self.call('/api/auth/register', 'POST', {'name': 'Partner', 'email': 'partner@example.com', 'phone': '+49 162 1234567', 'password': 'password123', 'role': 'provider'})
        _, admin = self.call('/api/auth/login', 'POST', {'email': 'info.machbar@gmx.de', 'password': 'admin-password-123'})
        self.assertEqual(self.call('/api/auth/register', 'POST', {'name': 'Fake', 'email': 'fake@example.com', 'phone': '+49 162 1234567', 'password': 'password123', 'role': 'admin'})[0], 400)
        status, job = self.call('/api/jobs', 'POST', {'category': 'Entrümpelung', 'title': 'Wohnung räumen', 'description': 'Bitte die gesamte Wohnung räumen.', 'postal_code': '69412', 'city': 'Eberbach'}, customer['token'])
        self.assertEqual(status, 201)
        self.assertEqual(len(self.call('/api/jobs', token=customer['token'])[1]['jobs']), 1)
        self.assertEqual(len(self.call('/api/jobs', token=provider['token'])[1]['jobs']), 0)
        self.assertEqual(self.call(f"/api/jobs/{job['id']}", 'PATCH', {'status': 'done'}, provider['token'])[0], 403)
        self.assertEqual(self.call(f"/api/jobs/{job['id']}", 'PATCH', {'provider_id': provider['user']['id']}, admin['token'])[0], 200)
        self.assertEqual(len(self.call('/api/jobs', token=provider['token'])[1]['jobs']), 1)
        self.assertEqual(self.call(f"/api/jobs/{job['id']}", 'PATCH', {'status': 'done'}, provider['token'])[0], 403)
        self.accept_offer(job['id'], provider, customer)
        for status in ('open','assigned','in_progress','done'):
            self.assertEqual(self.call(f"/api/jobs/{job['id']}", 'PATCH', {'status': status}, provider['token'])[0], 403)
        self.assertEqual(self.call(f"/api/jobs/{job['id']}", 'PATCH', {'status': 'done'}, admin['token'])[0], 200)
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
        _, admin = self.call('/api/auth/login', 'POST', {'email': 'info.machbar@gmx.de', 'password': 'admin-password-123'})
        saved = self.call('/api/jobs', token=admin['token'])[1]['jobs'][0]
        self.assertEqual(saved['id'], job['id'])
        self.assertEqual(saved['details'], body['details'])
        self.assertEqual(saved['description'], body['description'])
        for invalid in [[], {'work': 'invalid'}, {'notes': 'x' * 2001}, {'work': [None]}]:
            self.assertEqual(self.call('/api/jobs', 'POST', {**body, 'details': invalid})[0], 400)

    def test_multiple_services_photos_and_access_control(self):
        def register(name, role='customer'):
            return self.call('/api/auth/register', 'POST', {'name': name, 'email': name+'@example.com', 'phone': '+49 162 1234567', 'password': 'test-password-123', 'role': role})[1]
        owner, other, provider = register('owner'), register('other'), register('provider', 'provider')
        admin = self.call('/api/auth/login', 'POST', {'email': 'info.machbar@gmx.de', 'password': 'admin-password-123'})[1]
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
        before = self.call('/api/jobs', token=provider['token'])[1]['jobs'][0]
        self.assertFalse(before['contact_released'])
        self.assertEqual(before['photos'][0]['name'],'Foto 1')
        self.assertEqual(before['details']['services'],services)
        self.assertEqual(before['details']['scopes'],details['scopes'])
        for account in [owner, provider, admin]:
            with urlopen(Request(self.base+url, headers={'Authorization': 'Bearer '+account['token']})) as response:
                self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
                with Image.open(io.BytesIO(response.read())) as image:
                    self.assertEqual(image.size, (20, 20))
                    self.assertEqual(len(image.getexif()), 0)
        self.accept_offer(job['id'], provider, owner)
        with urlopen(Request(self.base+url, headers={'Authorization': 'Bearer '+provider['token']})) as response:
            self.assertEqual(response.status,200)
        # A bad photo rejects the whole request, even after an earlier valid photo.
        for photos in [[photo]*7, [photo, {**photo, 'data': 'data:image/png;base64,bm90YW5pbWFnZQ=='}], [{**photo, 'data': 'data:image/svg+xml;base64,PHN2Zz4='}]]:
            self.assertEqual(self.call('/api/jobs', 'POST', {**body, 'photos': photos}, owner['token'])[0], 400)
        self.assertEqual(len(self.call('/api/jobs', token=owner['token'])[1]['jobs']), 1)
        with server.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM job_photos').fetchone()[0], 1)

    def test_all_statuses_persist_until_admin_deletes_job_and_attachments(self):
        admin, owner, provider = self.admin(), self.account('owner'), self.account('provider','provider')
        body = {'category':'Reinigung','title':'Fenster reinigen','description':'Alle Fenster gründlich reinigen.','postal_code':'69412','city':'Eberbach'}
        photo_buffer = io.BytesIO()
        Image.new('RGB',(20,20),'blue').save(photo_buffer,format='PNG')
        photo = {'name':'fenster.png','data':'data:image/png;base64,'+base64.b64encode(photo_buffer.getvalue()).decode()}
        jobs = {}
        for status in ('open','assigned','in_progress','done'):
            job = self.call('/api/jobs','POST',{**body,'photos':[photo]},owner['token'])[1]
            path = f"/api/jobs/{job['id']}"
            self.assertEqual(self.call(path,'PATCH',{'status':status,'admin_note':'Interne Notiz'},admin['token'])[0],200)
            jobs[status] = job['id']
        # Old and completed jobs survive repeated startup and both admin read routes.
        with server.connect() as db:
            db.execute("UPDATE jobs SET created_at='2020-01-01 00:00:00'")
        server.init_db()
        for endpoint in ('/api/jobs','/api/admin/dashboard'):
            saved = self.call(endpoint,token=admin['token'])[1]['jobs']
            self.assertEqual({job['status']:job['id'] for job in saved},jobs)
        done_path = f"/api/jobs/{jobs['done']}"
        for token in (None,owner['token'],provider['token']):
            self.assertEqual(self.call(done_path,'DELETE',token=token)[0],403)
        self.assertEqual(self.call(done_path,token=admin['token'])[0],200)
        path = f"/api/jobs/{jobs['assigned']}"
        offer = self.call(path+'/offers','POST',{**self.offer_body(),'provider_id':provider['user']['id']},admin['token'])[1]
        saved = self.call(path,token=provider['token'])[1]['job']
        photo_url = saved['photos'][0]['url']
        # Disabled legacy mail records are cleaned only for the deleted job.
        with server.connect() as db:
            for event in (f"offer-{offer['id']}",f"decision-{offer['id']}-accepted",'unrelated'):
                db.execute('INSERT INTO email_outbox(event_key,recipient,subject,body) VALUES (?,?,?,?)',(event,'test@example.com','Test','Test'))
        self.assertEqual(self.call('/api/admin/notifications/retry','POST',{},admin['token'])[0],404)
        self.assertEqual(self.call(path,'DELETE',token=provider['token'])[0],403)
        self.assertEqual(self.call(path,'DELETE',token=admin['token'])[0],200)
        self.assertEqual(self.call(path,'DELETE',token=admin['token'])[0],404)
        for token in (owner['token'],provider['token'],admin['token']):
            self.assertEqual(self.call(path,token=token)[0],403)
            self.assertEqual(self.call(photo_url,token=token)[0],403)
        self.assertEqual(self.call(f"/api/offers/{offer['id']}/decision",'POST',{'decision':'accepted','selected_slot':0},owner['token'])[0],403)
        with server.connect() as db:
            for table in ('offers','job_photos','job_admin_notes'):
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table} WHERE job_id=?',(jobs['assigned'],)).fetchone()[0],0)
            self.assertEqual([row[0] for row in db.execute('SELECT event_key FROM email_outbox')],['unrelated'])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],3)
        self.assertEqual(self.call(done_path,'DELETE',token=admin['token'])[0],200)
        server.init_db()
        remaining = self.call('/api/admin/dashboard',token=admin['token'])[1]['jobs']
        self.assertEqual({job['id'] for job in remaining},{jobs['open'],jobs['in_progress']})

    def test_wsgi_for_pythonanywhere_preserves_auth_guest_access_and_delete(self):
        from .wsgi import application
        def wsgi_call(path, method='GET', body=None, token='', guest=''):
            payload = json.dumps(body).encode() if body is not None else b''
            environ = {'PATH_INFO':path,'REQUEST_METHOD':method,'CONTENT_LENGTH':str(len(payload)),
                       'HTTP_AUTHORIZATION':'Bearer '+token if token else '',
                       'HTTP_X_GUEST_TOKEN':guest,'wsgi.input':io.BytesIO(payload)}
            response = {}
            def start(status, headers):
                response['status'] = int(status.split()[0])
            content = b''.join(application(environ,start))
            return response['status'], json.loads(content)
        self.assertEqual(wsgi_call('/api/health'),(200,{'ok':True}))
        admin = self.admin()
        guest_job = wsgi_call('/api/jobs','POST',{'category':'Montage','title':'Regal montieren','description':'Ein Regal an der Wand befestigen.','postal_code':'69412','city':'Eberbach','contact_name':'Gast','contact_email':'guest@example.com'})
        self.assertEqual(guest_job[0],201)
        job = guest_job[1]
        path = f"/api/jobs/{job['id']}"
        self.assertEqual(wsgi_call(path)[0],403)
        self.assertEqual(wsgi_call(path,guest=job['guest_token'])[0],200)
        self.assertEqual(wsgi_call(path,'PATCH',{'admin_note':'WSGI funktioniert'},token=admin['token'])[0],200)
        self.assertEqual(wsgi_call('/api/admin/dashboard',token=admin['token'])[1]['jobs'][0]['admin_note'],'WSGI funktioniert')
        self.assertEqual(wsgi_call(path,'DELETE',guest=job['guest_token'])[0],403)
        self.assertEqual(wsgi_call(path,'DELETE',token=admin['token'])[0],200)
        self.assertEqual(wsgi_call(path,guest=job['guest_token'])[0],403)
        self.assertEqual(wsgi_call('/api/health','PUT')[0],405)

    def test_photo_byte_limit(self):
        with self.assertRaises(ValueError):
            server.prepare_photos([{'name': 'large.png', 'data': 'data:image/png;base64,'+base64.b64encode(b'x'*(server.MAX_PHOTO_BYTES+1)).decode()}])

    def test_admin_email_restriction_dashboard_and_private_notes(self):
        admin = self.call('/api/auth/login', 'POST', {'email': server.ADMIN_EMAIL, 'password': 'admin-password-123'})[1]
        for email in [server.ADMIN_EMAIL, ' INFO.MACHBAR@GMX.DE ']:
            self.assertEqual(self.call('/api/auth/register', 'POST', {'name':'Fake', 'email':email, 'phone':'+49 162 1234567','password':'password123', 'role':'customer'})[0],403)
        customer = self.call('/api/auth/register', 'POST', {'name':'Kunde','email':'customer@example.com','phone':'+49 162 1234567','password':'password123','role':'customer'})[1]
        provider = self.call('/api/auth/register', 'POST', {'name':'Partner','email':'provider@example.com','phone':'+49 162 1234567','password':'password123','role':'provider'})[1]
        for token in [None, customer['token'], provider['token']]:
            self.assertEqual(self.call('/api/admin/dashboard', token=token)[0],403)
        body = {'category':'Reinigung','title':'Fenster reinigen','description':'Alle Fenster im Haus reinigen.','postal_code':'69412','city':'Eberbach'}
        job = self.call('/api/jobs','POST',body,customer['token'])[1]
        status,snapshot = self.call('/api/admin/dashboard',token=admin['token'])
        self.assertEqual(status,200);self.assertEqual(len(snapshot['jobs']),1);self.assertEqual(snapshot['customers'],1)
        self.assertEqual(len(snapshot['providers']),1)
        path=f"/api/jobs/{job['id']}"
        self.assertEqual(self.call(path,'PATCH',{'admin_note':'Nur intern','provider_id':provider['user']['id'],'status':'assigned'},admin['token'])[0],200)
        self.assertEqual(self.call('/api/admin/dashboard',token=admin['token'])[1]['jobs'][0]['admin_note'],'Nur intern')
        self.assertNotIn('admin_note',self.call('/api/jobs',token=customer['token'])[1]['jobs'][0])
        self.assertNotIn('admin_note',self.call('/api/jobs',token=provider['token'])[1]['jobs'][0])
        self.assertEqual(self.call(path,'PATCH',{'provider_id':None,'status':'INVALID'},admin['token'])[0],400)
        self.assertEqual(self.call('/api/admin/dashboard',token=admin['token'])[1]['jobs'][0]['provider_id'],provider['user']['id'])
        # Even a legacy row with admin role cannot use admin APIs under another email.
        with server.connect() as db:
            db.execute("UPDATE users SET role='admin' WHERE id=?",(customer['user']['id'],))
        self.assertEqual(self.call('/api/admin/dashboard',token=customer['token'])[0],403)
        self.assertEqual(self.call('/api/providers',token=customer['token'])[0],403)
        self.assertEqual(self.call('/api/jobs',token=customer['token'])[0],403)
        self.assertEqual(self.call(path,'PATCH',{'status':'done'},customer['token'])[0],403)


if __name__ == '__main__':
    unittest.main()

"""WSGI entry point for PythonAnywhere, using the existing API routes."""
import io
from http import HTTPStatus
if __package__:
    from .server import Handler, init_db
else:
    from server import Handler, init_db


class WSGIHandler(Handler):
    def __init__(self, environ):
        self.path = environ.get('PATH_INFO', '/')
        self.headers = {
            'Authorization': environ.get('HTTP_AUTHORIZATION', ''),
            'Content-Length': environ.get('CONTENT_LENGTH') or '0',
            'X-Guest-Token': environ.get('HTTP_X_GUEST_TOKEN', ''),
        }
        self.rfile = environ['wsgi.input']
        self.wfile = io.BytesIO()
        self.response_status = 500
        self.response_headers = []

    def send_response(self, code, message=None):
        self.response_status = code

    def send_header(self, keyword, value):
        self.response_headers.append((keyword, value))

    def end_headers(self):
        pass


def application(environ, start_response):
    handler = WSGIHandler(environ)
    method = environ.get('REQUEST_METHOD', 'GET')
    if method not in ('GET', 'POST', 'PATCH', 'DELETE'):
        handler.send_header('Allow', 'GET, POST, PATCH, DELETE')
        handler.respond(405, {'error': 'Methode nicht erlaubt.'})
    else:
        handler.route(method)
    status = handler.response_status
    start_response(f'{status} {HTTPStatus(status).phrase}', handler.response_headers)
    return [handler.wfile.getvalue()]


init_db()

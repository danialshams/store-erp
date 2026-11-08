"""CSRF regression coverage against browser-originated unsafe requests."""
import os, tempfile
fd, path = tempfile.mkstemp(suffix='.db')
os.close(fd)
os.environ['DATABASE_URL'] = 'sqlite:///' + path
os.environ['APP_SECRET'] = 'test-secret-only'
from fastapi.testclient import TestClient
from api.index import app


def test_cross_site_post_without_origin_rejected():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post('/api/auth/login', json={
        'email': 'x@example.invalid', 'password': 'test',
    }, headers={'Sec-Fetch-Site': 'cross-site'})
    assert response.status_code == 403, response.text


def test_origin_scheme_downgrade_rejected():
    client = TestClient(app, base_url='https://testserver', raise_server_exceptions=False)
    response = client.post('/api/auth/login', json={
        'email': 'x@example.invalid', 'password': 'test',
    }, headers={'Origin': 'http://testserver', 'Host': 'testserver'})
    assert response.status_code == 403, response.text


def test_same_site_subdomain_without_origin_cannot_write_with_session_cookie():
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set('erp_session', 'fake-session-cookie')
    response = client.post('/api/auth/logout', headers={'Sec-Fetch-Site': 'same-site'})
    assert response.status_code == 403, response.text


def test_same_origin_fetch_metadata_is_not_blocked_by_csrf_guard():
    from api.security import csrf_guard
    from starlette.requests import Request
    scope = {'type': 'http', 'method': 'POST', 'scheme': 'https',
             'path': '/api/auth/logout', 'query_string': b'',
             'headers': [(b'host', b'testserver'), (b'sec-fetch-site', b'same-origin'),
                         (b'cookie', b'erp_session=fake-session-cookie')]}
    csrf_guard(Request(scope))

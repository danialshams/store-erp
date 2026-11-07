"""CSRF regression coverage against browser-originated unsafe requests."""
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

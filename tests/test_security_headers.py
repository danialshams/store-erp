"""Regression: security headers must be present even when middleware rejects early."""
from fastapi.testclient import TestClient
from api.index import app

EXPECTED = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "cache-control": "no-store",
}

def test_cross_origin_rejection_has_security_headers():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.invalid", "password": "invalid"},
        headers={"Origin": "https://attacker.example.invalid"},
    )
    assert response.status_code == 403, response.text
    for key, value in EXPECTED.items():
        assert response.headers.get(key) == value, (key, response.headers)

def test_normal_response_has_security_headers():
    response = TestClient(app).get("/api/ready")
    for key, value in EXPECTED.items():
        assert response.headers.get(key) == value, (key, response.headers)

"""PostgreSQL-backed API acceptance checks (never uses the SQLite test fixture).

Run only against an isolated CI PostgreSQL database containing demo migrations.
No writes are performed. PUBLIC_DEMO_ENABLED is scoped to this process.
"""
import os
assert os.environ.get("DATABASE_URL", "").startswith("postgresql"), "Requires PostgreSQL"
assert os.environ.get("PUBLIC_DEMO_ENABLED") == "true", "Public showroom must be enabled"
from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)
demo = "demo-erp-tenant-2026"

def test_ready_is_database_backed():
    r = client.get("/api/ready")
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "database": "connected"}

def test_public_showroom_routes_use_only_synthetic_tenant():
    info = client.get("/api/auth/me")
    assert info.status_code == 200, info.text
    assert info.json()["tenant_id"] == demo
    assert info.json()["public_demo"] is True
    for route, minimum in [
        ("/api/data/products?limit=1", 416),
        ("/api/data/variants?limit=1", 832),
        ("/api/data/customers?limit=1", 445),
        ("/api/data/stocks?limit=1", 4992),
    ]:
        r = client.get(route)
        assert r.status_code == 200, (route, r.text)
        assert r.json()["total"] >= minimum, (route, r.json())
        assert all(item["tenant_id"] == demo for item in r.json()["items"])

def test_stale_cookie_uses_public_read_only_tenant():
    stale = TestClient(app)
    stale.cookies.set("erp_session", "invalid.expired")
    r = stale.get("/api/auth/me")
    assert r.status_code == 200, r.text
    assert r.json()["tenant_id"] == demo
    assert r.json()["public_demo"] is True
    r = stale.post("/api/data/products", json={"name": "Must not be created"})
    assert r.status_code in (401, 403), r.text

def test_public_mutations_and_cross_site_requests_are_denied():
    r = client.post("/api/data/products", json={"name": "Not allowed"})
    assert r.status_code == 403, r.text
    r = client.post("/api/data/products", json={"name": "Not allowed"},
                    headers={"sec-fetch-site": "cross-site"})
    assert r.status_code == 403, r.text
    r = client.post("/api/data/products", json={"name": "Not allowed"},
                    headers={"origin": "https://attacker.example.invalid"})
    assert r.status_code == 403, r.text

def test_double_entry_integrity_over_actual_postgresql_demo():
    r = client.get("/api/ledger/integrity")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] > 0, body
    assert body["invalid_count"] == 0, body
    assert client.get("/api/ledger/integrity?start=2026-12-31&end=2026-01-01").status_code == 422

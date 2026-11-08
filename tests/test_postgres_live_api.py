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
    assert body["journal_count"] > 0, body
    assert body["issue_count"] == 0, body
    assert client.get("/api/ledger/integrity?start=2026-12-31&end=2026-01-01").status_code == 422


def test_public_showroom_never_returns_other_tenants_across_core_modules():
    # Verify returned rows, not just the tenant ID in /auth/me.
    # A one-row smoke check can miss leakage on subsequent pages.
    for resource in (
        "products", "variants", "customers", "suppliers", "warehouses",
        "stocks", "sales", "purchases", "movements",
    ):
        response = client.get(f"/api/data/{resource}", params={"limit": 50})
        assert response.status_code == 200, (resource, response.text)
        payload = response.json()
        assert isinstance(payload.get("items"), list), (resource, payload)
        for row in payload["items"]:
            assert row["tenant_id"] == demo, (resource, row.get("id"))

    invoices = client.get("/api/invoices", params={"limit": 50})
    assert invoices.status_code == 200, invoices.text
    invoice_payload = invoices.json()
    for row in invoice_payload.get("items", []):
        assert row["tenant_id"] == demo, row.get("id")


def test_public_showroom_rejects_every_mutation_method_on_postgresql():
    # Must not rely solely on frontend read-only controls.
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        path = "/api/data/products" if method in ("POST", "PUT") else "/api/data/products/nonexistent-demo-id"
        response = client.request(
            method, path,
            json={"name": "Public write must fail"},
        )
        assert response.status_code == 403, (
            method, response.status_code, response.text
        )
        # No cross-tenant data should be exposed in denial responses.
        assert "database" not in response.text.lower(), (method, response.text)


def test_public_showroom_isolation_across_pagination_boundaries():
    """Check later pages too: a first-page-only tenant test misses leaks."""
    for resource in ("products", "variants", "customers", "stocks", "sales", "purchases"):
        first = client.get(f"/api/data/{resource}", params={"page": 1, "limit": 25})
        assert first.status_code == 200, (resource, first.text)
        total = first.json()["total"]
        assert total > 25, (resource, total)
        last_page = (total + 24) // 25
        for page in (1, 2, last_page):
            response = client.get(f"/api/data/{resource}", params={"page": page, "limit": 25})
            assert response.status_code == 200, (resource, page, response.text)
            payload = response.json()
            assert payload["total"] == total, (resource, page, payload)
            assert payload["page"] == page, (resource, page, payload)
            assert payload["items"], (resource, page, payload)
            assert all(row["tenant_id"] == demo for row in payload["items"]), (
                resource, page
            )
        beyond = client.get(f"/api/data/{resource}", params={"page": last_page + 1, "limit": 25})
        assert beyond.status_code == 200, (resource, beyond.text)
        assert beyond.json()["items"] == [], resource


def test_stale_session_cookie_cannot_mutate_postgresql_showroom():
    """Expired/invalid cookies may preview demo reads, never write any resource."""
    stale = TestClient(app, raise_server_exceptions=False)
    stale.cookies.set("erp_session", "invalid.expired")
    before = stale.get("/api/data/products", params={"limit": 1})
    assert before.status_code == 200, before.text
    assert before.json()["items"][0]["tenant_id"] == demo
    count = before.json()["total"]

    for method, path in (
        ("POST", "/api/data/products"),
        ("PUT", "/api/integrations/sms"),
        ("PATCH", "/api/data/products/nonexistent-demo-id"),
        ("DELETE", "/api/data/products/nonexistent-demo-id"),
    ):
        response = stale.request(method, path, json={"name": "Forbidden stale-session write"})
        assert response.status_code in (401, 403), (method, response.status_code, response.text)

    after = stale.get("/api/data/products", params={"limit": 1})
    assert after.status_code == 200, after.text
    assert after.json()["total"] == count
    assert all(row["tenant_id"] == demo for row in after.json()["items"])

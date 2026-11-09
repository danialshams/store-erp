"""PostgreSQL showroom regression: existing records in editable modules stay immutable.

Run against the disposable CI PostgreSQL database seeded by migrations.
A nonexistent ID is not sufficient evidence: target persisted demo records.
"""
import os

assert os.environ.get("DATABASE_URL", "").startswith("postgresql"), "Requires PostgreSQL"
assert os.environ.get("PUBLIC_DEMO_ENABLED") == "true", "Requires showroom mode"

import pytest
from fastapi.testclient import TestClient
from api.index import app

DEMO_TENANT = "demo-erp-tenant-2026"
EDITABLE_RESOURCES = (
    "categories", "products", "variants", "warehouses",
    "suppliers", "customers", "price-lists", "cash-accounts",
    "tax-rates", "shipments",
)


@pytest.mark.parametrize("resource", EDITABLE_RESOURCES)
def test_existing_demo_records_are_immutable_with_anonymous_and_stale_sessions(resource):
    with TestClient(app, raise_server_exceptions=False) as client:
        before = client.get(f"/api/data/{resource}", params={"page": 1, "limit": 1})
        assert before.status_code == 200, (resource, before.text)
        data = before.json()
        assert data["total"] > 0, f"Missing seeded record for {resource}"
        record = data["items"][0]
        assert record["tenant_id"] == DEMO_TENANT
        record_id = record["id"]

        for cookie in (None, "invalid.expired"):
            if cookie:
                client.cookies.set("erp_session", cookie)
            else:
                client.cookies.clear()
            for method in ("PATCH", "DELETE"):
                response = client.request(
                    method,
                    f"/api/data/{resource}/{record_id}",
                    json={"name": "UNAUTHORIZED CHANGE"},
                )
                assert response.status_code in (401, 403), (
                    resource, cookie, method, response.status_code, response.text
                )
            create = client.post(f"/api/data/{resource}", json={"name": "UNAUTHORIZED CREATE"})
            assert create.status_code in (401, 403), (
                resource, cookie, create.status_code, create.text
            )

        client.cookies.clear()
        after = client.get(f"/api/data/{resource}", params={"page": 1, "limit": 1})
        assert after.status_code == 200, (resource, after.text)
        assert after.json()["total"] == data["total"], resource
        assert after.json()["items"][0] == record, resource

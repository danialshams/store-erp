"""PostgreSQL acceptance: public showroom cannot alter *existing* demo records.

Run with the isolated PostgreSQL CI database and PUBLIC_DEMO_ENABLED=true.
The test deliberately targets a real record instead of a nonexistent ID:
a 404 on a fake ID would not prove that authorization protects real data.
"""
import os

assert os.environ.get("DATABASE_URL", "").startswith("postgresql"), "Requires PostgreSQL"
assert os.environ.get("PUBLIC_DEMO_ENABLED") == "true", "Requires public showroom"

from fastapi.testclient import TestClient
from api.index import app


def test_anonymous_existing_product_is_immutable():
    with TestClient(app) as client:
        before = client.get("/api/data/products", params={"page": 1, "limit": 1})
        assert before.status_code == 200, before.text
        body = before.json()
        assert body["total"] > 0
        product = body["items"][0]
        assert product["tenant_id"] == "demo-erp-tenant-2026"
        product_id = product["id"]

        for method in ("PATCH", "DELETE"):
            response = client.request(
                method,
                f"/api/data/products/{product_id}",
                json={"name": "UNAUTHORIZED PUBLIC EDIT"},
            )
            assert response.status_code == 403, (method, response.status_code, response.text)

        after = client.get("/api/data/products", params={"page": 1, "limit": 1})
        assert after.status_code == 200, after.text
        assert after.json()["total"] == body["total"]
        # Do not rely on pagination order staying constant: locate the original ID.
        found = client.get("/api/data/products", params={"page": 1, "limit": 500})
        assert found.status_code == 200, found.text
        same = next((p for p in found.json()["items"] if p["id"] == product_id), None)
        assert same is not None, product_id
        assert same == product, (product, same)

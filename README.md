# ERP فروشگاهی — Portable Retail ERP

نسخهٔ توسعه و تست اولیهٔ یک ERP فارسی/راست‌به‌چپ برای کسب‌وکارهای چندکاربره و چندانباره.

> **وضعیت: هستهٔ عملیاتی قابل آزمایش، نه نسخهٔ آمادهٔ استفادهٔ تجاری.** امکانات تکمیل‌نشده و گیت‌های انتشار در انتهای این فایل مشخص شده‌اند. ورود به محیط واقعی بدون ممیزی امنیتی، تست PostgreSQL و پشتیبان‌گیری توصیه نمی‌شود.

## Technology

- Python 3.12+, FastAPI, SQLAlchemy 2, PostgreSQL 14+ (production), SQLite (local automated tests only)
- Dependency-light HTML/CSS/JavaScript frontend (no framework lock-in), Persian RTL, Vazirmatn
- HTTP-only signed session cookie, PBKDF2-SHA256 password hashing (600,000 iterations), tenant-scoped API queries, RBAC checks
- 30 relational tables with FKs, unique constraints, integer TOMAN money, ISO timestamps; UI formats Jalali dates
- Stock adjustments and transitions use PostgreSQL advisory transaction locks and row locks, nonnegative/free-stock checks, movement ledger and audit records
- Docker Compose + PostgreSQL for self-hosting; Vercel Python adapter for temporary hosting

## Current working functionality

| Area | Status and details |
|---|---|
| Authentication | Sign-up, sign-in, HttpOnly session, logout, tenant creation |
| Organizations | Manage organization profile, switch memberships, invite existing users, roles |
| Dashboard | Sales, revenue received, inventory value, receivables, low stock, seven-day chart |
| Catalog | CRUD categories, products, variants, SKU uniqueness, price snapshots, archive |
| Warehouses | Multiwarehouse CRUD, stock adjustment, reserved stock, movements |
| Transfers | Draft → ship → receive, non-negative stock enforced |
| Purchasing | Suppliers, purchase orders, items, goods receipts (full/partial), idempotency support |
| Sales | Customer CRUD, sales orders, reserve/confirm/fulfill/cancel, price snapshot |
| Payments | Manual payment registration, idempotency, accounting cash entries, notifications |
| Returns | Sales & supplier returns linked to their orders; returned quantity validation |
| Logistics | Shipment CRUD, carrier, tracking, status |
| Pricing | Retail/wholesale variant prices, customer groups, editable price lists/items |
| Finance/reporting | Cash accounts, payments, simple account entries; inventory/sales/margin/receivable/payable reports + CSV |
| Settings/audit | Company profile, roles/invites, audit event records |

**What is not production-complete:** real bank gateway/webhook integration, full double-entry bookkeeping/tax invoice issuance, cycle count reconciliation UI, batch/serial FEFO stock deduction, returns refund settlement, shipping provider integrations, external shop sync, email/SMS invite delivery, robust stock allocation at scale, full audit/RLS defense-in-depth, password reset/MFA, server-side report exports/pagination beyond 1000 rows. Those must be built and tested before commercial launch. **Do not represent this version as a fully finished 14-module ERP.**

## Local development (SQLite only for quick UI checks)

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export APP_SECRET='a-long-random-string-for-development'
uvicorn api.index:app --reload
# visit http://localhost:8000
```

SQLite is used **only if `DATABASE_URL` is absent in local dev**. On Vercel or production, `DATABASE_URL` is required and the app deliberately refuses to use ephemeral SQLite.

## PostgreSQL Docker development / self-hosted VPS

```bash
cp .env.example .env
# Replace both POSTGRES_PASSWORD and APP_SECRET with random secrets
# docker compose loads these from .env
docker compose up --build -d
```

This creates the PostgreSQL service and app service. Data survives container restarts in `erp_pgdata`. Set reverse-proxy HTTPS, `COOKIE_SECURE=true`, backups and monitoring before production. **Never commit `.env` or database credentials to Git.**

## Schema migration on a managed PostgreSQL

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/0001_schema.sql
```

For new DBs, `python -m api.init_db` creates the same ORM tables and indexes. For future changes use versioned migrations (e.g. Alembic); do not rely on `create_all` to change existing tables. The current SQL migration was generated from the exact SQLAlchemy models and contains all 30 tables. Run migration once before Vercel production deployment.

## Temporary Vercel hosting

The repo has a `vercel.json` routing the Python ASGI entrypoint and a static frontend. To deploy with Git connected:

1. Push the source into a **dedicated new** GitHub repository (for example `danialshams/store-erp`). Do not mix it into existing CRM/shop applications.
2. Create Vercel project from that repository, framework/adapter FastAPI.
3. Configure `DATABASE_URL` as the **PostgreSQL connection string** (secret), `APP_SECRET` as a cryptographically random 64+ character secret, `COOKIE_SECURE=true`.
4. Apply migrations to the database before serving traffic.
5. Build, smoke-test `/api/health`, test signup and all transactional operations with two tenants and role permissions. Keep production deployment disabled until checks pass.

**Moving from Vercel to VPS:** copy source unchanged, export PostgreSQL via `pg_dump --format=custom`, restore using `pg_restore`, set the same environment variables, configure nginx/TLS and run Docker Compose. File images currently require externally hosted HTTPS URLs; add S3-compatible storage before production media uploads.

## API

- `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`
- `/api/data/{resource}` list/create, `/api/data/{resource}/{id}` update/delete (only allowed reference data)
- `/api/stock/adjust`, `/api/transfers`, `/api/transfers/{id}/{ship|receive|cancel}`
- `/api/purchases`, `/api/purchases/{id}/receive`
- `/api/sales`, `/api/sales/{id}/{confirm|fulfill|cancel}`
- `/api/payments`, `/api/returns`, `/api/dashboard`, `/api/reports`, `/api/settings`
- `/api/members`, `/api/invites`, `/api/auth/accept-invite`, `/api/organizations`
- `/api/docs` OpenAPI browser documentation

Every protected resource is scoped by the tenant identity taken from the signed cookie; incoming tenant IDs are **not trusted**. Direct stock edits are not exposed through CRUD.

## Tests / QA

```bash
PYTHONPATH=. pytest -q tests/test_flows.py
node --check public/app.js
python -m py_compile api/*.py
```

`tests/test_flows.py` tests independent tenants, SKU uniqueness, stock movement, transfers, purchase receive, reserved inventory, sale fulfilment, payment idempotency and returns. `tests/browser_smoke.py` exercises desktop and mobile UI with a local API bridge for environments restricting browser network access; requires a running local server. Do not confuse these smoke tests with a full security and production PostgreSQL audit.

## Security & deployment gates

- Rotate app secret, use encrypted environment storage, HTTPS and private PostgreSQL credentials.
- Enforce rate limits on login, add CSRF defense-in-depth and strict server-side request schemas.
- Add tenant-scoped **database-level RLS** or an app-level PostgreSQL role/policy design as defense in depth; current tenant isolation is enforced in API code.
- Verify PostgreSQL concurrency/locking with parallel-worker load tests, backups and restoration.
- Build more automated tests for role permissions, invoice/payment reconciliation, partial receipts/returns and multi-tenant data references.
- Perform accessibility, RTL, mobile QA and operational monitoring before launching.

Copyright and license: user project source. No external commercial dependencies bundled.
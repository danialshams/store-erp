# ERP فروشگاهی — Portable Retail ERP

نسخهٔ توسعه و تست اولیهٔ یک ERP فارسی/راست‌به‌چپ برای کسب‌وکارهای چندکاربره و چندانباره.

> **وضعیت: هستهٔ عملیاتی قابل آزمایش، نه نسخهٔ آمادهٔ استفادهٔ تجاری.** امکانات تکمیل‌نشده و گیت‌های انتشار در انتهای این فایل مشخص شده‌اند. ورود به محیط واقعی بدون ممیزی امنیتی، تست PostgreSQL و پشتیبان‌گیری توصیه نمی‌شود.

## Public showroom mode (temporary, read-only)

To demonstrate the full panel without a sign-in page, apply the versioned migrations in numeric order, including `migrations/0003_seed_public_demo.sql`, then set `PUBLIC_DEMO_ENABLED=true` on the preview deployment. This is an additive, idempotent seed: it inserts a dedicated tenant `demo-erp-tenant-2026`, a synthetic unloginable demo user, and thousands of fictional records, and it does not delete or modify existing customers.

With this flag enabled, anonymous **GET/HEAD** requests are restricted to the demo tenant and the UI shows all sections with explicit read-only messaging. Anonymous **POST/PATCH/PUT/DELETE** calls return HTTP 403. Real signed-in sessions retain their original tenant identity and permissions. A visitor cannot access a real tenant without a valid signed user session. Set `PUBLIC_DEMO_ENABLED=false` later to restore the regular sign-in screen and standard authentication flow; never remove authorization from the backend.

Seeded sections include catalog/categories/variants, customers, suppliers, warehouses, batches, stock and movements, transfers, purchases and lines, sales and lines, invoices, manual payments, returns, shipments, price lists, cash accounts, tax rates, team, notifications, and audit logs. Every contact is fictional and uses `example.invalid` where an email is shown. The demo cannot modify balances, initiate transactions, send messages, or trigger external integrations.

**Status:** the public showroom is a demonstration of the currently implemented ERP workflows. It does not mean all commercial launch gates are finished.

## Technology

- Python 3.12+, FastAPI, SQLAlchemy 2, PostgreSQL 14+ (production), SQLite (local automated tests only)
- Dependency-light HTML/CSS/JavaScript frontend (no framework lock-in), Persian RTL, Vazirmatn
- HTTP-only signed session cookie, PBKDF2-SHA256 password hashing (600,000 iterations), tenant-scoped API queries, RBAC checks
- PostgreSQL schema with versioned additive migrations (including the original 32 tables and later extensions), FKs, unique constraints, integer TOMAN money, ISO timestamps; UI formats Jalali dates
- Stock adjustments and transitions use PostgreSQL advisory transaction locks and row locks, nonnegative/free-stock checks, movement ledger and audit records
- Docker Compose + PostgreSQL for self-hosting; Vercel Python adapter for temporary hosting

## Current working functionality

| Area | Status and details |
|---|---|
| Authentication | Sign-up, sign-in, HttpOnly session, logout, tenant creation |
| Organizations | Manage organization profile, switch memberships, invite existing users, roles |
| Dashboard | Sales, revenue received, inventory value, receivables, low stock, seven-day chart |
| Catalog | CRUD categories, products, variants, SKU uniqueness, price snapshots, archive |
| Warehouses | Multiwarehouse CRUD, stock adjustment, reserved stock, movements; transactional cycle count reconciliation with stale-snapshot checks |
| Transfers | Draft → ship → receive, non-negative stock enforced |
| Purchasing | Suppliers, purchase orders, items, goods receipts (full/partial), idempotency support |
| Sales | Customer CRUD, sales orders, reserve/confirm/fulfill/cancel, price snapshot |
| Payments | Manual payment registration, idempotency, accounting cash entries, notifications |
| Returns | Sales & supplier returns linked to their orders; returned quantity validation; manual customer refund and supplier reimbursement settlement with audit and caps |
| Logistics | Shipment CRUD, carrier, tracking, status |
| Pricing | Retail/wholesale variant prices, customer groups, editable price lists/items |
| Finance/reporting | Cash accounts, payments, manual return settlement, simple account entries; immutable internal invoice snapshots and printable HTML; inventory/sales/margin/receivable/payable reports + CSV |
| Settings/audit | Company profile, roles/invites, audit event records |

**What is not independently accepted for commercial production:** external gateway/webhook, official tax integrations, shipping provider, external shop sync, email/SMS and storage integrations require external services. Double-entry accounting, batch/serial FEFO, stock allocation under concurrency, tenant isolation, CSRF, session security, report exports and browser workflows require comprehensive end-to-end acceptance evidence; implementation or passing unit tests alone is insufficient. Those must be built and tested before commercial launch. **Do not represent this version as a fully finished 14-module ERP.**

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
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/0002_invoices.sql
# Then apply every subsequent numbered migration in migrations/ in ascending order.
# Do not re-run an unverified non-idempotent migration against a populated database.
```

For new DBs, `python -m api.init_db` creates the same ORM tables and indexes. For future changes use versioned migrations (e.g. Alembic); do not rely on `create_all` to change existing tables. Migration 0001 creates the original 30 tables, and additive migration 0002 adds 2 invoice snapshot tables. These are NOT the complete current schema: later migrations add further tables and policies. Use all applicable numbered migrations in order on a fresh database. Run migration once before Vercel production deployment.

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
- `/api/payments`, `/api/returns`, `/api/returns/{id}/settlement`, `/api/returns/{id}/settle`
- `/api/invoices`, `/api/invoices/{id}`, `/api/invoices/{id}/print`
- `/api/stock/cycle-sheet`, `/api/stock/cycle-count`, `/api/ready`, `/api/dashboard`, `/api/reports`, `/api/settings`
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
- Verify login rate limits, CSRF defense-in-depth and strict server-side request schemas against real browser and PostgreSQL flows.
- Audit the existing PostgreSQL RLS policies, role permissions and tenant-scoped composite foreign keys against every new table and endpoint; verify isolation using separate database roles and multiple tenants.
- Verify PostgreSQL concurrency/locking with parallel-worker load tests, backups and restoration.
- Build more automated tests for role permissions, invoice/payment reconciliation, partial receipts/returns and multi-tenant data references.
- Perform accessibility, RTL, mobile QA and operational monitoring before launching.

Copyright and license: user project source. No external commercial dependencies bundled.
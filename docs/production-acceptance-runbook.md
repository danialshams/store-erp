# Production acceptance and PostgreSQL migration runbook

> This is a release gate, not a claim of production readiness. Follow [issue #3](https://github.com/danialshams/store-erp/issues/3) for unresolved work.

## Source of truth

The repository README contains historical table counts and migration examples. **Do not provision production from its abbreviated two-migration example.** The current CI bootstrap in `.github/workflows/ci.yml` is the authoritative tested ordering. It includes the base schema, invoices, demo seed, tenant RLS, ledger, integrations, traceability, revocable sessions, partial fulfillment, tenant-integrity constraints and enriched demo data. Keep CI and any future migration runner in sync.

Before deployment, inventory migrations and verify applied versions on a disposable PostgreSQL instance. A seed is not a schema migration; never execute public demo seeds against a real customer tenant or expose production credentials in CI. Avoid running `api.init_db` as a substitute for a versioned migration of an existing database.

## Mandatory release checks

1. **Isolation:** create two *synthetic* tenants; assert tenant A cannot read, enumerate, modify or delete B's rows across all resources and pagination. Check DB-level RLS using a non-owner, non-BYPASSRLS role. Verify composite tenant foreign keys, forged identifiers and stale/invalid sessions. Public showroom requests must resolve only to the fictional tenant; anonymous mutations must return 403 and leave DB state unchanged.
2. **Security:** exercise authentication, logout/revocation, role permissions, Origin/CSRF validation, session cookie flags and cross-tenant reference attempts in both API tests and a real browser. Do not equate an HTTP 403 with proof that the underlying row was unchanged; compare database snapshots.
3. **Inventory:** parallel purchase receipts, FEFO allocation, expiry handling, serial uniqueness, transfers, partial fulfillment, cancellation and returns. Assert no negative free stock, no duplicate serial allocation and consistent stock-movement totals after retries.
4. **Finance:** for every posted journal, check positive equal debit/credit sums, valid tenant-owned accounts and immutability. Reconcile each invoice, payment, partial refund and supplier settlement to receivable/payable and cash ledger balances. Test duplicate idempotency keys and concurrent settlements.
5. **Workflow:** execute registration → product → purchase → partial receipt → sale → partial fulfillment → payment → return → refund on an isolated throwaway PostgreSQL tenant, then verify all resulting rows and balances. Never run destructive acceptance flows against customer data.
6. **UI:** run keyboard and accessibility checks, RTL layout, mobile touch and desktop browsers, all forms and readonly showroom previews. Confirm demo interactions never persist.
7. **Operations:** restore a `pg_dump` into a fresh disposable database and compare constraints, RLS, data counts and critical financial totals. Verify recovery time, backup retention, secret rotation, health endpoints, monitoring, indexes and realistic load.
8. **Release:** require green GitHub Actions on the exact PR head, review migration safety, merge only after checks, verify the Vercel deployment corresponds to the merged SHA, then check `/api/ready` and representative GET/forbidden-write requests.

## VPS migration rehearsal (no VPS purchase required)

Use local Docker PostgreSQL as a stand-in for the future VPS. Export a consistent custom-format PostgreSQL dump, restore to a new empty database, apply the same least-privilege DB roles, verify RLS and extensions, start the application with fresh environment variables, then run the full acceptance suite. Document downtime, DNS cutover, rollback and backup encryption before any real migration. Passing a local rehearsal does **not** mean a purchased VPS or external provider is connected.

## External service boundary

Payment gateway, SMS, email, S3, carrier and external storefront credentials may remain absent. Their UI must explicitly show disabled/unconfigured state. Adapters must fail closed without pretending to deliver messages, accept payments or sync external systems. Use contract tests with fake providers; label these as mocks, not live integrations.

**Release decision:** do not mark issue #3 complete until each non-external gate has a dated CI run, commit SHA and reproducible evidence.

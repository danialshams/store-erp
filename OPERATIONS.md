# Backup, restore, hosting and incident response

The ERP is portable: FastAPI, SQLAlchemy and standard PostgreSQL. No Vercel-specific database dependency is required.

## Backup
Use a protected CI runner or the future VPS. Configure a read-capable **PostgreSQL** `DATABASE_URL`. Run:

```bash
bash scripts/backup.sh /secure/backups/erp-$(date -u +%Y%m%d).dump
```

The dump is compressed and verified before being atomically moved; file mode 0600. It contains **all customers, password hashes and transactions**. Never publish, send in chat, commit to GitHub or leave backups under a public web root. Encrypt off-site storage and restrict operator roles. Until external storage is configured, schedule local backups yourself; no unattended S3 uploading is claimed.

## Restore rehearsal (non-destructive)
Provision an **entirely separate empty PostgreSQL database**, configure `RESTORE_DATABASE_URL` distinct from `DATABASE_URL`, and run:

```bash
RESTORE_DATABASE_URL='postgresql://operator:***@localhost:5432/erp_restore' \
 bash scripts/restore.sh /secure/backups/erp-YYYYMMDD.dump
```

The script rejects the same source URL, non-empty target, unreadable backup or incomplete restored schema. It never drops or overwrites existing business data. GitHub Actions repeats a backup and restore on an isolated PostgreSQL container with table, fulfillment and same-tenant FK counts.

## Future VPS migration
1. Create a fresh PostgreSQL 17 database; install Docker and HTTPS reverse proxy.
2. Take a verified backup during a short write-maintenance window on Vercel.
3. Restore into a new empty VPS database and compare record counts, RLS policies, FK constraints and latest journal balances.
4. Configure `DATABASE_URL`, fresh `APP_SECRET` (existing sessions will log out), `COOKIE_SECURE=true`, `APP_ENV=production`, and (temporary) `PUBLIC_DEMO_ENABLED=true` only if public showroom remains desired.
5. Run the Dockerized app with TLS proxy and a separate persistent Postgres volume. Validate `/api/ready`, public read-only demo and authenticated cross-tenant tests.
6. Point domain/DNS to VPS after verification. Keep rollback copy in read-only storage. Reopen writes only after comparisons pass.

## Provider integrations
Payment, SMS, email, shipping carrier, S3, storefront connectors are **configuration-only, disabled** until credentials and verified provider-specific webhooks are added. Never claim a transaction was settled by a gateway based on a manual ERP payment record.

## Operations
Add provider-native PITR/backups and monitoring when VPS/storage is purchased. The existence of these scripts is not evidence that an unattended off-site retention or scheduled production backup is already active.

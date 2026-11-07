-- 0005: balanced double-entry general ledger, additive and tenant isolated.
BEGIN;
CREATE TABLE IF NOT EXISTS ledger_accounts (
  id VARCHAR(36) PRIMARY KEY,tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  created_at TIMESTAMPTZ NOT NULL,code VARCHAR(20) NOT NULL,name VARCHAR(180) NOT NULL,
  kind VARCHAR(24) NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (tenant_id,code)
);
CREATE INDEX IF NOT EXISTS ix_ledger_accounts_tenant_id ON ledger_accounts(tenant_id);
CREATE TABLE IF NOT EXISTS journals (
  id VARCHAR(36) PRIMARY KEY,tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  created_at TIMESTAMPTZ NOT NULL,number VARCHAR(80) NOT NULL,
  source_key VARCHAR(180),memo TEXT NOT NULL DEFAULT '',journal_date DATE NOT NULL,
  actor_id VARCHAR(36) NOT NULL REFERENCES users(id),
  UNIQUE (tenant_id,number),UNIQUE (tenant_id,source_key)
);
CREATE INDEX IF NOT EXISTS ix_journals_tenant_id ON journals(tenant_id);
CREATE TABLE IF NOT EXISTS journal_lines (
  id VARCHAR(36) PRIMARY KEY,tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
  created_at TIMESTAMPTZ NOT NULL,journal_id VARCHAR(36) NOT NULL REFERENCES journals(id),
  account_id VARCHAR(36) NOT NULL REFERENCES ledger_accounts(id),
  debit BIGINT NOT NULL DEFAULT 0,credit BIGINT NOT NULL DEFAULT 0,note VARCHAR(250),
  CONSTRAINT ck_journal_lines_positive CHECK (
     (debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0))
);
CREATE INDEX IF NOT EXISTS ix_journal_lines_tenant_id ON journal_lines(tenant_id);
CREATE INDEX IF NOT EXISTS ix_journal_lines_journal_id ON journal_lines(journal_id);
DO $$
DECLARE tab text;
BEGIN
 FOREACH tab IN ARRAY ARRAY['ledger_accounts','journals','journal_lines']
 LOOP
  EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',tab);
  EXECUTE format('DROP POLICY IF EXISTS erp_tenant_guard ON public.%I',tab);
  EXECUTE format(
   'CREATE POLICY erp_tenant_guard ON public.%I FOR ALL TO PUBLIC USING (tenant_id = current_setting(''erp.tenant_id'',true)) WITH CHECK (tenant_id = current_setting(''erp.tenant_id'',true))',tab);
 END LOOP;
END $$;
DO $
BEGIN
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='store_erp_app_rw') THEN
  GRANT SELECT,INSERT,UPDATE,DELETE ON public.ledger_accounts,
    public.journals,public.journal_lines TO store_erp_app_rw;
 END IF;
END $;
COMMIT;

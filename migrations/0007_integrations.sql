-- Migration 0007: metadata for not-yet-purchased external integrations.
BEGIN;
CREATE TABLE IF NOT EXISTS integrations (
 id VARCHAR(36) PRIMARY KEY,tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
 created_at TIMESTAMPTZ NOT NULL,kind VARCHAR(35) NOT NULL,
 provider VARCHAR(80) NOT NULL DEFAULT '',settings JSON NOT NULL DEFAULT '{}',
 enabled BOOLEAN NOT NULL DEFAULT FALSE,UNIQUE (tenant_id,kind)
);
CREATE INDEX IF NOT EXISTS ix_integrations_tenant_id ON integrations(tenant_id);
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS erp_tenant_guard ON integrations;
CREATE POLICY erp_tenant_guard ON integrations FOR ALL TO PUBLIC
 USING (tenant_id = current_setting('erp.tenant_id',true))
 WITH CHECK (tenant_id = current_setting('erp.tenant_id',true));
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='store_erp_app_rw') THEN
  EXECUTE 'GRANT SELECT,INSERT,UPDATE,DELETE ON public.integrations TO store_erp_app_rw';
 END IF;
END $$;
COMMIT;

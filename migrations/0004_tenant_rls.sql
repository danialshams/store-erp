-- Migration 0004: enforce PostgreSQL row-level tenant isolation.
-- Apply ONLY after application code sets transaction-local erp.tenant_id.
-- Exempt users, tenants, members and invites: login, invitation acceptance
-- and organization lookup require these before a tenant has been selected.
-- Access to these four remains tightly scoped in the authenticated API.
BEGIN;
DO $$
DECLARE tab text;
BEGIN
 FOR tab IN
   SELECT table_name FROM information_schema.columns
    WHERE table_schema='public' AND column_name='tenant_id'
      AND table_name NOT IN ('members','invites')
 LOOP
   EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',tab);
   EXECUTE format('DROP POLICY IF EXISTS erp_tenant_guard ON public.%I',tab);
   EXECUTE format(
    'CREATE POLICY erp_tenant_guard ON public.%I FOR ALL TO PUBLIC USING (tenant_id = current_setting(''erp.tenant_id'',true)) WITH CHECK (tenant_id = current_setting(''erp.tenant_id'',true))',tab);
 END LOOP;
END $$;
COMMIT;

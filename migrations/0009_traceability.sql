-- 0009: FEFO lot movement ledger and unit-serial tracking.
BEGIN;
CREATE TABLE IF NOT EXISTS lot_movements (
 id VARCHAR(36) PRIMARY KEY,tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
 created_at TIMESTAMPTZ NOT NULL,warehouse_id VARCHAR(36) NOT NULL REFERENCES warehouses(id),
 variant_id VARCHAR(36) NOT NULL REFERENCES variants(id),
 batch_id VARCHAR(36) NOT NULL REFERENCES stock_batches(id),
 delta INTEGER NOT NULL CHECK(delta <> 0),
 reason VARCHAR(40) NOT NULL,reference_id VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_lot_movements_tenant_id ON lot_movements(tenant_id);
CREATE INDEX IF NOT EXISTS ix_lot_movements_batch_ref ON lot_movements(tenant_id,reference_id,batch_id);
CREATE TABLE IF NOT EXISTS serial_items (
 id VARCHAR(36) PRIMARY KEY,tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
 created_at TIMESTAMPTZ NOT NULL,warehouse_id VARCHAR(36) NOT NULL REFERENCES warehouses(id),
 variant_id VARCHAR(36) NOT NULL REFERENCES variants(id),serial VARCHAR(150) NOT NULL,
 status VARCHAR(25) NOT NULL DEFAULT 'in_stock',reference_id VARCHAR(36),
 UNIQUE(tenant_id,serial)
);
CREATE INDEX IF NOT EXISTS ix_serial_items_tenant_id ON serial_items(tenant_id);
CREATE INDEX IF NOT EXISTS ix_serial_items_status ON serial_items(tenant_id,warehouse_id,variant_id,status);
DO $$
DECLARE tab text;
BEGIN
 FOREACH tab IN ARRAY ARRAY['lot_movements','serial_items'] LOOP
  EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',tab);
  EXECUTE format('DROP POLICY IF EXISTS erp_tenant_guard ON public.%I',tab);
  EXECUTE format('CREATE POLICY erp_tenant_guard ON public.%I FOR ALL TO PUBLIC USING (tenant_id = current_setting(''erp.tenant_id'',true)) WITH CHECK (tenant_id = current_setting(''erp.tenant_id'',true))',tab);
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='store_erp_app_rw') THEN
  EXECUTE 'GRANT SELECT,INSERT,UPDATE,DELETE ON public.lot_movements,public.serial_items TO store_erp_app_rw';
 END IF;
END $$;
COMMIT;

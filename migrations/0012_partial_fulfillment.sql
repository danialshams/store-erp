-- 0012: safe partial fulfillment with per-line shipped counters.
BEGIN;
ALTER TABLE public.sales_lines ADD COLUMN IF NOT EXISTS fulfilled INTEGER NOT NULL DEFAULT 0;
UPDATE public.sales_lines l SET fulfilled=l.quantity
 FROM public.sales_orders o
 WHERE l.order_id=o.id AND l.tenant_id=o.tenant_id
   AND o.status='fulfilled' AND l.fulfilled<l.quantity;
DO $$
DECLARE constraint_name text;
BEGIN
 FOR constraint_name IN
   SELECT conname FROM pg_constraint
    WHERE conrelid='public.sales_lines'::regclass AND contype='c'
      AND pg_get_constraintdef(oid) LIKE '%returned%'
 LOOP
  EXECUTE format('ALTER TABLE public.sales_lines DROP CONSTRAINT %I',constraint_name);
 END LOOP;
END $$;
ALTER TABLE public.sales_lines DROP CONSTRAINT IF EXISTS ck_salesline_fulfillment;
ALTER TABLE public.sales_lines ADD CONSTRAINT ck_salesline_fulfillment
 CHECK(quantity>0 AND price>=0 AND returned>=0 AND fulfilled>=0
       AND returned<=fulfilled AND fulfilled<=quantity);
CREATE TABLE IF NOT EXISTS fulfillments (
 id VARCHAR(36) PRIMARY KEY,tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
 created_at TIMESTAMPTZ NOT NULL,order_id VARCHAR(36) NOT NULL REFERENCES sales_orders(id),
 warehouse_id VARCHAR(36) NOT NULL REFERENCES warehouses(id),
 number VARCHAR(60) NOT NULL,status VARCHAR(25) NOT NULL DEFAULT 'shipped',
 items JSON NOT NULL DEFAULT '[]',revenue BIGINT NOT NULL DEFAULT 0,
 cost BIGINT NOT NULL DEFAULT 0,carrier VARCHAR(120),tracking_number VARCHAR(120),
 UNIQUE(tenant_id,number),CHECK(revenue >= 0 AND cost >= 0)
);
CREATE INDEX IF NOT EXISTS ix_fulfillments_tenant_id ON fulfillments(tenant_id);
CREATE INDEX IF NOT EXISTS ix_fulfillments_order_id ON fulfillments(tenant_id,order_id);
ALTER TABLE fulfillments ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS erp_tenant_guard ON fulfillments;
CREATE POLICY erp_tenant_guard ON fulfillments FOR ALL TO PUBLIC
 USING(tenant_id=current_setting('erp.tenant_id',true))
 WITH CHECK(tenant_id=current_setting('erp.tenant_id',true));
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='store_erp_app_rw') THEN
  EXECUTE 'GRANT SELECT,INSERT,UPDATE,DELETE ON public.fulfillments TO store_erp_app_rw';
 END IF;
END $$;
COMMIT;

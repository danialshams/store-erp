-- 0015: tenant-scoped sales tax rate, frozen invoice VAT, credit terms.
BEGIN;
ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS tax_amount BIGINT NOT NULL DEFAULT 0;
ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS tax_rate_id VARCHAR(36) REFERENCES tax_rates(id);
ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS payment_terms VARCHAR(20) NOT NULL DEFAULT 'immediate';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS tax_amount BIGINT NOT NULL DEFAULT 0;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS tax_name VARCHAR(120) NOT NULL DEFAULT '';
ALTER TABLE sales_orders DROP CONSTRAINT IF EXISTS ck_sales_tax_positive;
ALTER TABLE sales_orders ADD CONSTRAINT ck_sales_tax_positive
 CHECK(tax_amount>=0 AND payment_terms IN ('immediate','credit'));
ALTER TABLE invoices DROP CONSTRAINT IF EXISTS ck_invoice_tax_total;
ALTER TABLE invoices ADD CONSTRAINT ck_invoice_tax_total
 CHECK(subtotal-discount+tax_amount=total);
CREATE UNIQUE INDEX IF NOT EXISTS ux_tax_rates_tenant_id_id ON tax_rates(tenant_id,id);
ALTER TABLE sales_orders DROP CONSTRAINT IF EXISTS fk_sales_orders_tax_rate_id_tenant;
ALTER TABLE sales_orders ADD CONSTRAINT fk_sales_orders_tax_rate_id_tenant
 FOREIGN KEY (tenant_id,tax_rate_id) REFERENCES tax_rates(tenant_id,id)
 NOT VALID;
ALTER TABLE sales_orders VALIDATE CONSTRAINT fk_sales_orders_tax_rate_id_tenant;
COMMIT;

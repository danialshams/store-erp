-- ERP additive migration 0002: immutable internal sales invoice snapshots
-- Apply after migrations/0001_schema.sql on PostgreSQL.
BEGIN;
CREATE TABLE IF NOT EXISTS invoices (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ NOT NULL,
  order_id VARCHAR(36) NOT NULL REFERENCES sales_orders(id),
  number VARCHAR(48) NOT NULL,
  customer_name VARCHAR(220) NOT NULL DEFAULT '',
  customer_address TEXT NOT NULL DEFAULT '',
  subtotal BIGINT NOT NULL,
  discount BIGINT NOT NULL DEFAULT 0,
  total BIGINT NOT NULL,
  issuer_id VARCHAR(36) NOT NULL REFERENCES users(id),
  CONSTRAINT uq_invoice_tenant_order UNIQUE (tenant_id, order_id),
  CONSTRAINT uq_invoice_tenant_number UNIQUE (tenant_id, number),
  CONSTRAINT ck_invoice_amounts CHECK (subtotal >= 0 AND discount >= 0 AND total >= 0)
);
CREATE INDEX IF NOT EXISTS ix_invoices_tenant_id ON invoices (tenant_id);
CREATE TABLE IF NOT EXISTS invoice_lines (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ NOT NULL,
  invoice_id VARCHAR(36) NOT NULL REFERENCES invoices(id),
  variant_id VARCHAR(36) NOT NULL REFERENCES variants(id),
  sku_snapshot VARCHAR(100) NOT NULL,
  name_snapshot VARCHAR(250) NOT NULL,
  quantity INTEGER NOT NULL,
  price BIGINT NOT NULL,
  CONSTRAINT ck_invoice_line CHECK (quantity > 0 AND price >= 0)
);
CREATE INDEX IF NOT EXISTS ix_invoice_lines_tenant_id ON invoice_lines (tenant_id);
CREATE INDEX IF NOT EXISTS ix_invoice_lines_invoice_id ON invoice_lines (invoice_id);
COMMIT;

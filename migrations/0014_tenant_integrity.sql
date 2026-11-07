-- 0014: DB-enforced same-tenant references for every tenant-owned relationship.
-- Creates composite uniqueness on targets then validates existing rows. Any wrong
-- tenant link ABORTS the transaction; no existing records are rewritten.
BEGIN;
DO $$
DECLARE row record; constraint_name text;
BEGIN
 FOR row IN SELECT DISTINCT ref_table FROM (VALUES
    ('categories','parent_id','categories'),
    ('products','category_id','categories'),
    ('variants','product_id','products'),
    ('stocks','warehouse_id','warehouses'),
    ('stocks','variant_id','variants'),
    ('stock_batches','warehouse_id','warehouses'),
    ('stock_batches','variant_id','variants'),
    ('movements','warehouse_id','warehouses'),
    ('movements','variant_id','variants'),
    ('transfers','source_id','warehouses'),
    ('transfers','destination_id','warehouses'),
    ('transfers','variant_id','variants'),
    ('purchase_orders','supplier_id','suppliers'),
    ('purchase_orders','warehouse_id','warehouses'),
    ('purchase_lines','order_id','purchase_orders'),
    ('purchase_lines','variant_id','variants'),
    ('sales_orders','customer_id','customers'),
    ('sales_orders','warehouse_id','warehouses'),
    ('sales_lines','order_id','sales_orders'),
    ('sales_lines','variant_id','variants'),
    ('payments','order_id','sales_orders'),
    ('payments','purchase_id','purchase_orders'),
    ('returns','order_id','sales_orders'),
    ('returns','purchase_id','purchase_orders'),
    ('returns','variant_id','variants'),
    ('returns','warehouse_id','warehouses'),
    ('shipments','order_id','sales_orders'),
    ('invoices','order_id','sales_orders'),
    ('invoice_lines','invoice_id','invoices'),
    ('invoice_lines','variant_id','variants'),
    ('price_items','list_id','price_lists'),
    ('price_items','variant_id','variants'),
    ('account_entries','account_id','cash_accounts'),
    ('journal_lines','journal_id','journals'),
    ('journal_lines','account_id','ledger_accounts'),
    ('lot_movements','warehouse_id','warehouses'),
    ('lot_movements','variant_id','variants'),
    ('lot_movements','batch_id','stock_batches'),
    ('serial_items','warehouse_id','warehouses'),
    ('serial_items','variant_id','variants'),
    ('fulfillments','order_id','sales_orders'),
    ('fulfillments','warehouse_id','warehouses')
 ) AS m(child_table,child_field,ref_table)
 LOOP
  EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS %I ON public.%I(tenant_id,id)',
                 'ux_'||row.ref_table||'_tenant_id_id', row.ref_table);
 END LOOP;
 FOR row IN SELECT child_table,child_field,ref_table FROM (VALUES
    ('categories','parent_id','categories'),
    ('products','category_id','categories'),
    ('variants','product_id','products'),
    ('stocks','warehouse_id','warehouses'),
    ('stocks','variant_id','variants'),
    ('stock_batches','warehouse_id','warehouses'),
    ('stock_batches','variant_id','variants'),
    ('movements','warehouse_id','warehouses'),
    ('movements','variant_id','variants'),
    ('transfers','source_id','warehouses'),
    ('transfers','destination_id','warehouses'),
    ('transfers','variant_id','variants'),
    ('purchase_orders','supplier_id','suppliers'),
    ('purchase_orders','warehouse_id','warehouses'),
    ('purchase_lines','order_id','purchase_orders'),
    ('purchase_lines','variant_id','variants'),
    ('sales_orders','customer_id','customers'),
    ('sales_orders','warehouse_id','warehouses'),
    ('sales_lines','order_id','sales_orders'),
    ('sales_lines','variant_id','variants'),
    ('payments','order_id','sales_orders'),
    ('payments','purchase_id','purchase_orders'),
    ('returns','order_id','sales_orders'),
    ('returns','purchase_id','purchase_orders'),
    ('returns','variant_id','variants'),
    ('returns','warehouse_id','warehouses'),
    ('shipments','order_id','sales_orders'),
    ('invoices','order_id','sales_orders'),
    ('invoice_lines','invoice_id','invoices'),
    ('invoice_lines','variant_id','variants'),
    ('price_items','list_id','price_lists'),
    ('price_items','variant_id','variants'),
    ('account_entries','account_id','cash_accounts'),
    ('journal_lines','journal_id','journals'),
    ('journal_lines','account_id','ledger_accounts'),
    ('lot_movements','warehouse_id','warehouses'),
    ('lot_movements','variant_id','variants'),
    ('lot_movements','batch_id','stock_batches'),
    ('serial_items','warehouse_id','warehouses'),
    ('serial_items','variant_id','variants'),
    ('fulfillments','order_id','sales_orders'),
    ('fulfillments','warehouse_id','warehouses')
 ) AS m(child_table,child_field,ref_table)
 LOOP
  constraint_name='fk_'||row.child_table||'_'||row.child_field||'_tenant';
  IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname=constraint_name AND
                conrelid=format('public.%I',row.child_table)::regclass) THEN
   EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY
                   (tenant_id,%I) REFERENCES public.%I (tenant_id,id) NOT VALID',
                  row.child_table,constraint_name,row.child_field,row.ref_table);
  END IF;
  EXECUTE format('ALTER TABLE public.%I VALIDATE CONSTRAINT %I',
                 row.child_table,constraint_name);
 END LOOP;
END $$;
COMMIT;

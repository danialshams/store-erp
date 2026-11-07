-- Synthetic demo traceability history and unit-level serial identities.
BEGIN;
INSERT INTO lot_movements(id,tenant_id,created_at,warehouse_id,variant_id,batch_id,
                          delta,reason,reference_id)
SELECT md5('demo-lot-opening:'||b.id),b.tenant_id,b.created_at,
       b.warehouse_id,b.variant_id,b.id,b.quantity,'opening',NULL
FROM stock_batches b
WHERE b.tenant_id='demo-erp-tenant-2026' AND b.quantity>0
ON CONFLICT(id) DO NOTHING;
INSERT INTO serial_items(id,tenant_id,created_at,warehouse_id,variant_id,serial,status,reference_id)
SELECT md5('demo-serial:'||v.id||':'||n.i),v.tenant_id,
       NOW()-(n.i*INTERVAL '1 day'),s.warehouse_id,v.id,
       'DEMO-SERIAL-'||v.sku||'-'||lpad(n.i::text,3,'0'),
       'in_stock',NULL
FROM variants v JOIN stocks s ON s.tenant_id=v.tenant_id AND s.variant_id=v.id
CROSS JOIN LATERAL generate_series(1,LEAST(s.quantity,5)) n(i)
WHERE v.tenant_id='demo-erp-tenant-2026' AND v.track_serial=TRUE
 AND s.warehouse_id='dw-0001'
ON CONFLICT (id) DO NOTHING;
COMMIT;

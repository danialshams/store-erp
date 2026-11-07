-- 0013: historical demo orders represented as multiple actual shipment manifests.
-- Additive and repeatable, no modification of real customer data or inventory.
BEGIN;
WITH shipments AS (
 SELECT o.id AS order_id,o.tenant_id,o.warehouse_id,o.created_at,
        o.total,o.status,sl.id AS line_id,sl.variant_id,sl.quantity,
        sl.price,sl.cost_snapshot,
        (sl.quantity*sl.price)::BIGINT AS gross_line,
        SUM((sl.quantity*sl.price)::BIGINT) OVER(PARTITION BY o.id) AS gross_order,
        SUM((sl.quantity*sl.price)::BIGINT) OVER(
          PARTITION BY o.id ORDER BY sl.id ROWS UNBOUNDED PRECEDING) AS gross_after,
        ROW_NUMBER() OVER(PARTITION BY o.id ORDER BY sl.id) AS part_number
 FROM sales_orders o JOIN sales_lines sl
   ON sl.order_id=o.id AND sl.tenant_id=o.tenant_id
 WHERE o.tenant_id='demo-erp-tenant-2026' AND o.status='fulfilled'
), amounts AS (
 SELECT *,
   CASE WHEN gross_order>0 THEN
    (total*gross_after/gross_order)-(total*(gross_after-gross_line)/gross_order)
   ELSE 0 END AS revenue_allocated
 FROM shipments
)
INSERT INTO fulfillments(id,tenant_id,created_at,order_id,warehouse_id,number,
                         status,items,revenue,cost,carrier,tracking_number)
SELECT 'dful-'||line_id,tenant_id,created_at+(part_number*INTERVAL '45 minutes'),
       order_id,warehouse_id,'DEMO-FUL-'||line_id,
       CASE WHEN part_number=1 THEN 'delivered' ELSE 'shipped' END,
       json_build_array(json_build_object('line_id',line_id,'variant_id',variant_id,
          'quantity',quantity,'unit_price',price,'cost_snapshot',cost_snapshot)),
       revenue_allocated,quantity*cost_snapshot,
       CASE WHEN part_number=1 THEN 'پست پیشتاز' ELSE 'تیپاکس' END,
       'DEMO-TRACK-FUL-'||line_id
FROM amounts
ON CONFLICT(id) DO NOTHING;
COMMIT;

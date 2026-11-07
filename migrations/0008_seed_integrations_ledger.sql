-- Demo integrations are permanently disabled until a real provider exists.
-- Adds realistic cost-of-goods pairs to synthetic ledger records.
BEGIN;
INSERT INTO integrations(id,tenant_id,created_at,kind,provider,settings,enabled)
SELECT 'dint-'||kind,'demo-erp-tenant-2026',NOW()-INTERVAL '80 days',
       kind,provider,settings::json,FALSE
FROM (VALUES
 ('payment','zarinpal','{"callback_url":"https://example.invalid/payment/callback"}'),
 ('sms','kavenegar','{"sender":"DEMO-SENDER"}'),
 ('email','smtp','{"sender_email":"no-reply@example.invalid"}'),
 ('storage','parspack','{"bucket":"demo-bucket","endpoint":"https://storage.example.invalid"}'),
 ('shipping','post','{"origin_city":"تهران"}'),
 ('storefront','nextjs','{"store_name":"فروشگاه نمونه","base_url":"https://store.example.invalid"}')
) t(kind,provider,settings)
ON CONFLICT (tenant_id,kind) DO NOTHING;
WITH sales_cogs AS (
 SELECT j.id AS journal_id,COALESCE(SUM(sl.quantity*sl.cost_snapshot),0)::bigint AS val
 FROM journals j JOIN sales_orders o ON j.source_key='demo-sale:'||o.id
 JOIN sales_lines sl ON sl.order_id=o.id
 WHERE j.tenant_id='demo-erp-tenant-2026' AND sl.tenant_id='demo-erp-tenant-2026'
 GROUP BY j.id
)
INSERT INTO journal_lines(id,tenant_id,created_at,journal_id,account_id,debit,credit,note)
SELECT md5(journal_id||':cogs:dr'),'demo-erp-tenant-2026',NOW(),
       journal_id,'dla-5000',val,0,'بهای تمام‌شده فروش نمایشی'
FROM sales_cogs WHERE val>0
UNION ALL
SELECT md5(journal_id||':cogs:cr'),'demo-erp-tenant-2026',NOW(),
       journal_id,'dla-1300',0,val,'خروج موجودی فروش نمایشی'
FROM sales_cogs WHERE val>0
ON CONFLICT (id) DO NOTHING;
COMMIT;

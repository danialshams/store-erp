-- Rich financial demo; synthetic tenant only. Repeatable without deletes.
BEGIN;
INSERT INTO ledger_accounts(id,tenant_id,created_at,code,name,kind,active)
SELECT 'dla-'||code,'demo-erp-tenant-2026',NOW()-INTERVAL '200 days',code,name,kind,true
FROM (VALUES
 ('1010','صندوق نقدی','asset'),('1020','بانک و کارتخوان','asset'),
 ('1200','حساب‌های دریافتنی','asset'),('1300','موجودی کالا','asset'),
 ('2000','حساب‌های پرداختنی','liability'),('3000','سرمایه و موجودی افتتاحیه','equity'),
 ('4000','درآمد فروش','revenue'),('4100','برگشت از فروش','revenue'),
 ('5000','بهای تمام‌شده فروش','expense'),('6000','تعدیل و کسری انبار','expense')
) AS chart(code,name,kind)
ON CONFLICT (tenant_id,code) DO NOTHING;
WITH doc AS (
 SELECT 'dj-sale-'||substring(id from 4) AS id,id AS ref,
        'DEMO-LEDGER-S-'||substring(id from 4) AS number,
        'demo-sale:'+id AS source_key,
        'ثبت فروش نمونه شماره '||number AS memo,created_at::date AS event_date,created_at
 FROM sales_orders WHERE tenant_id='demo-erp-tenant-2026' AND status='fulfilled' AND total>0
 UNION ALL
 SELECT 'dj-po-'||substring(id from 5),id,'DEMO-LEDGER-P-'||substring(id from 5),
        'demo-purchase:'+id,'دریافت خرید نمونه '||number,created_at::date,created_at
 FROM purchase_orders WHERE tenant_id='demo-erp-tenant-2026' AND status IN ('received','partial') AND total>0
 UNION ALL
 SELECT 'dj-pay-'||id,id,'DEMO-LEDGER-PAY-'||id,
        'demo-payment:'+id,'دریافت یا پرداخت نمونه',created_at::date,created_at
 FROM payments WHERE tenant_id='demo-erp-tenant-2026' AND amount>0
)
INSERT INTO journals(id,tenant_id,created_at,number,source_key,memo,journal_date,actor_id)
SELECT id,'demo-erp-tenant-2026',created_at,number,source_key,memo,event_date,'demo-erp-user-public'
FROM doc ON CONFLICT (id) DO NOTHING;
WITH posting AS (
 SELECT j.id AS jid,j.tenant_id,'1200' AS debit_acct,'4000' AS credit_acct,o.total AS value
 FROM journals j JOIN sales_orders o ON j.source_key='demo-sale:'||o.id
 WHERE j.tenant_id='demo-erp-tenant-2026' AND o.total>0
 UNION ALL
 SELECT j.id,j.tenant_id,'1300','2000',
        (SELECT COALESCE(sum(ln.received*ln.cost),0) FROM purchase_lines ln WHERE ln.order_id=o.id) AS value
 FROM journals j JOIN purchase_orders o ON j.source_key='demo-purchase:'||o.id
 WHERE j.tenant_id='demo-erp-tenant-2026'
 UNION ALL
 SELECT j.id,j.tenant_id,CASE WHEN p.order_id IS NOT NULL THEN '1020' ELSE '2000' END,
        CASE WHEN p.order_id IS NOT NULL THEN '1200' ELSE '1020' END,p.amount
 FROM journals j JOIN payments p ON j.source_key='demo-payment:'||p.id
 WHERE j.tenant_id='demo-erp-tenant-2026' AND p.amount>0
)
INSERT INTO journal_lines(id,tenant_id,created_at,journal_id,account_id,debit,credit,note)
SELECT md5(jid||'-dr'),'demo-erp-tenant-2026',NOW()-INTERVAL '30 days',
       jid,a.id,value,0,'بدهکار نمونه'
FROM posting p JOIN ledger_accounts a ON a.tenant_id=p.tenant_id AND a.code=p.debit_acct
WHERE value>0
UNION ALL
SELECT md5(jid||'-cr'),'demo-erp-tenant-2026',NOW()-INTERVAL '30 days',
       jid,a.id,0,value,'بستانکار نمونه'
FROM posting p JOIN ledger_accounts a ON a.tenant_id=p.tenant_id AND a.code=p.credit_acct
WHERE value>0
ON CONFLICT (id) DO NOTHING;
COMMIT;

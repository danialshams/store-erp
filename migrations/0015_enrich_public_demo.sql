-- Additional entirely fictional ERP showroom examples.
-- Each record is permanently bound to demo-erp-tenant-2026; idempotent inserts only.
-- No real contacts, customer IDs, account identifiers, or credentials are generated.
BEGIN;
INSERT INTO products (id,tenant_id,name,category_id,description,image_url,active,archived,created_at)
SELECT 'show-p-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['گوشی هوشمند','لپ‌تاپ','هدفون بی‌سیم','ساعت هوشمند','شارژر','کیبورد مکانیکی','دوربین دیجیتال','دستگاه قهوه‌ساز','عطر','پیراهن','کفش','کیف','لوازم تحریر','اسپیکر','روتر اینترنت','ماشین اصلاح'])[1+((i-97)%16)]||' سری '||(ARRAY['Nova','Studio','Ultra','Air','Prime','Essential','Classic','Max'])[1+((i-97)/16)%8]||' شماره '||i,
'dc-'||lpad((1+((i-97)%16))::text,4,'0'),
'این مشخصات و قیمت‌ها صرفاً برای نمایش قابلیت‌های ERP فروشگاهی تولید شده‌اند؛ کالای واقعی وجود ندارد.',
NULL,true,false,NOW()-(i%95)*INTERVAL '1 day'
FROM generate_series(97,416) i
ON CONFLICT (id) DO NOTHING;

INSERT INTO variants(id,tenant_id,product_id,name,sku,barcode,unit,purchase_cost,retail_price,wholesale_price,low_stock,track_batch,track_serial,active,created_at)
SELECT 'show-v-'||lpad(i::text,5,'0'),'demo-erp-tenant-2026',
'show-p-'||lpad((97+((i-193)/2))::text,4,'0'),
CASE WHEN i%2=1 THEN 'استاندارد' ELSE 'نسخه پلاس' END,
'SHOW-SKU-'||lpad(i::text,5,'0'),
'626199'||lpad(i::text,7,'0'),'عدد',
230000+(i*1750),450000+(i*3200),420000+(i*2600),
8+(i%11), i%13=0,i%17=0,true,NOW()-(i%85)*INTERVAL '1 day'
FROM generate_series(193,832) i ON CONFLICT (id) DO NOTHING;

INSERT INTO customers(id,tenant_id,name,phone,email,address,group_name,credit_limit,created_at)
SELECT 'show-cu-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['مریم','علی','مهتاب','رضا','سارا','آرین','الناز','نوید','بهار','کاوه','نرگس','پوریا','هستی','بردیا','پارسا','یاسمین'])[1+((i-126)%16)]||' '||
(ARRAY['شریفی','کریمی','رحمانی','زمانی','حسینی','پارسا','راد','صالحی','نوری','محمدی','احمدی','موسوی'])[1+(((i-126)/16)%12)]||' - '||i,
NULL,'showroom-customer-'||i||'@example.invalid',
'نشانی نمونه و غیرواقعی - شهر آزمایشی',
(ARRAY['عادی','وفادار','عمده','ویژه'])[1+(i%4)],
(i%7)*1800000,NOW()-(i%110)*INTERVAL '1 day'
FROM generate_series(126,445) i ON CONFLICT (id) DO NOTHING;

INSERT INTO suppliers(id,tenant_id,name,phone,email,address,notes,created_at)
SELECT 'show-su-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['بازرگانی ارم','پخش افق','تأمین تجارت','گروه سپهر','پارس کالا','شرکت آراد'])[1+(i%6)]||' - نمایندگی نمونه '||i,
NULL,'showroom-supplier-'||i||'@example.invalid','آدرس فرضی تأمین‌کننده',
'رکورد ساختگی برای پیش‌نمایش خرید و مدیریت تأمین‌کنندگان',NOW()-(i%80)*INTERVAL '1 day'
FROM generate_series(25,54) i ON CONFLICT (id) DO NOTHING;

INSERT INTO stocks(id,tenant_id,warehouse_id,variant_id,quantity,reserved,created_at)
SELECT 'show-st-'||w||'-'||i,'demo-erp-tenant-2026',
'dw-'||lpad(w::text,4,'0'),'show-v-'||lpad(i::text,5,'0'),
CASE WHEN i%11=0 THEN 1 ELSE 10+((i*3+w)%30) END,
CASE WHEN i%11=0 THEN 0 WHEN i%17=0 THEN 2 ELSE 0 END,
NOW()-INTERVAL '50 days'
FROM generate_series(1,6) w CROSS JOIN generate_series(193,832) i
ON CONFLICT (id) DO NOTHING;

INSERT INTO movements(id,tenant_id,warehouse_id,variant_id,delta,reason,reference_id,note,actor_id,created_at)
SELECT 'show-mv-'||w||'-'||i,'demo-erp-tenant-2026',
'dw-'||lpad(w::text,4,'0'),'show-v-'||lpad(i::text,5,'0'),
CASE WHEN i%11=0 THEN 1 ELSE 10+((i*3+w)%30) END,
'opening',NULL,'موجودی افتتاحیه ساختگی جهت نمایش گردش انبار',
'demo-erp-user-public',NOW()-INTERVAL '50 days'
FROM generate_series(1,6) w CROSS JOIN generate_series(193,832) i
ON CONFLICT (id) DO NOTHING;

INSERT INTO stock_batches(id,tenant_id,warehouse_id,variant_id,lot,expiry_date,quantity,created_at)
SELECT 'show-lot-'||w||'-'||i,'demo-erp-tenant-2026',
'dw-'||lpad(w::text,4,'0'),'show-v-'||lpad(i::text,5,'0'),
'SHOW-LOT-'||lpad(i::text,5,'0'),
CURRENT_DATE + (15+(i%20)*9) * INTERVAL '1 day',
CASE WHEN i%11=0 THEN 1 ELSE 10+((i*3+w)%30) END,
NOW()-INTERVAL '45 days'
FROM generate_series(1,2) w CROSS JOIN generate_series(193,832) i
WHERE i%13=0
ON CONFLICT (id) DO NOTHING;

INSERT INTO serial_items(id,tenant_id,warehouse_id,variant_id,serial,status,reference_id,created_at)
SELECT 'show-serial-'||i||'-'||n,'demo-erp-tenant-2026',
'dw-0001','show-v-'||lpad(i::text,5,'0'),
'SHOW-SERIAL-'||i||'-'||n,'in_stock',NULL,NOW()-INTERVAL '30 days'
FROM generate_series(193,832) i CROSS JOIN generate_series(1,2) n WHERE i%17=0
ON CONFLICT (id) DO NOTHING;

WITH a AS (
SELECT i, 193+(((i-141)*2)%640) v1, 194+(((i-141)*2)%640) v2,
1+(i%3) q1, 1+(i%2) q2, (i%4)*9000 discount
FROM generate_series(141,460) i), calc AS (
SELECT *, ((450000+v1*3200)*q1+(450000+v2*3200)*q2-discount)::bigint AS total FROM a)
INSERT INTO sales_orders(id,tenant_id,customer_id,warehouse_id,number,channel,status,total,paid,discount,created_at)
SELECT 'show-so-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
'show-cu-'||lpad((126+((i-141)%320))::text,4,'0'),
'dw-'||lpad((1+(i%6))::text,4,'0'),
'SHOW-SO-'||lpad(i::text,5,'0'),
(ARRAY['retail','wholesale','online','pos'])[1+(i%4)],
(ARRAY['fulfilled','confirmed','draft','cancelled'])[1+(i%4)],
total, CASE WHEN i%4 in (0,1) THEN CASE WHEN i%3=0 THEN total ELSE total/2 END ELSE 0 END,
discount,NOW()-(i%100)*INTERVAL '1 day'-(i%8)*INTERVAL '2 hour'
FROM calc ON CONFLICT (id) DO NOTHING;

WITH a AS (
SELECT i, 193+(((i-141)*2)%640) v1, 194+(((i-141)*2)%640) v2, 1+(i%3) q1, 1+(i%2) q2 FROM generate_series(141,460) i)
INSERT INTO sales_lines(id,tenant_id,order_id,variant_id,quantity,returned,fulfilled,price,cost_snapshot,created_at)
SELECT 'show-sl-'||i||'-1','demo-erp-tenant-2026','show-so-'||lpad(i::text,4,'0'),
'show-v-'||lpad(v1::text,5,'0'),q1,0,CASE WHEN i%4=0 THEN q1 ELSE 0 END,
450000+v1*3200,230000+v1*1750,NOW()-(i%100)*INTERVAL '1 day'
FROM a
UNION ALL SELECT 'show-sl-'||i||'-2','demo-erp-tenant-2026','show-so-'||lpad(i::text,4,'0'),
'show-v-'||lpad(v2::text,5,'0'),q2,0,CASE WHEN i%4=0 THEN q2 ELSE 0 END,
450000+v2*3200,230000+v2*1750,NOW()-(i%100)*INTERVAL '1 day'
FROM a ON CONFLICT (id) DO NOTHING;

WITH a AS (
SELECT i,193+(((i-91)*3)%640) v1,194+(((i-91)*3)%640) v2,2+(i%4) q1,1+(i%3) q2
FROM generate_series(91,270) i), calc AS (
SELECT *, ((230000+v1*1750)*q1+(230000+v2*1750)*q2)::bigint total FROM a)
INSERT INTO purchase_orders(id,tenant_id,supplier_id,warehouse_id,number,status,total,paid,created_at)
SELECT 'show-po-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
'show-su-'||lpad((25+((i-91)%30))::text,4,'0'),
'dw-'||lpad((1+(i%6))::text,4,'0'),
'SHOW-PO-'||lpad(i::text,5,'0'),
(ARRAY['received','partial','draft','received'])[1+(i%4)],
total,CASE WHEN i%4=2 THEN 0 WHEN i%3=0 THEN total ELSE total/2 END,
NOW()-(i%90)*INTERVAL '1 day'
FROM calc ON CONFLICT (id) DO NOTHING;

WITH a AS (
SELECT i,193+(((i-91)*3)%640) v1,194+(((i-91)*3)%640) v2,2+(i%4) q1,1+(i%3) q2
FROM generate_series(91,270) i)
INSERT INTO purchase_lines(id,tenant_id,order_id,variant_id,quantity,received,cost,created_at)
SELECT 'show-pol-'||i||'-1','demo-erp-tenant-2026','show-po-'||lpad(i::text,4,'0'),
'show-v-'||lpad(v1::text,5,'0'),q1,CASE WHEN i%4=2 THEN 0 WHEN i%4=1 THEN q1-1 ELSE q1 END,
230000+v1*1750,NOW()-(i%90)*INTERVAL '1 day'
FROM a
UNION ALL
SELECT 'show-pol-'||i||'-2','demo-erp-tenant-2026','show-po-'||lpad(i::text,4,'0'),
'show-v-'||lpad(v2::text,5,'0'),q2,CASE WHEN i%4=2 THEN 0 WHEN i%4=1 THEN 0 ELSE q2 END,
230000+v2*1750,NOW()-(i%90)*INTERVAL '1 day'
FROM a ON CONFLICT (id) DO NOTHING;

INSERT INTO payments(id,tenant_id,order_id,purchase_id,amount,method,idempotency_key,actor_id,created_at)
SELECT 'show-pay-'||s.id,'demo-erp-tenant-2026',s.id,NULL,s.paid,
(ARRAY['cash','card','transfer','online'])[1+((CAST(substring(s.id from 9) AS INTEGER))%4)],
'show-sale-payment-'||s.number,'demo-erp-user-public',s.created_at+INTERVAL '3 hours'
FROM sales_orders s WHERE s.tenant_id='demo-erp-tenant-2026' AND s.id LIKE 'show-so-%' AND s.paid>0
ON CONFLICT (id) DO NOTHING;

INSERT INTO payments(id,tenant_id,order_id,purchase_id,amount,method,idempotency_key,actor_id,created_at)
SELECT 'show-pay-'||p.id,'demo-erp-tenant-2026',NULL,p.id,p.paid,
(ARRAY['card','transfer','cash'])[1+((CAST(substring(p.id from 9) AS INTEGER))%3)],
'show-purchase-payment-'||p.number,'demo-erp-user-public',p.created_at+INTERVAL '1 day'
FROM purchase_orders p WHERE p.tenant_id='demo-erp-tenant-2026' AND p.id LIKE 'show-po-%' AND p.paid>0
ON CONFLICT (id) DO NOTHING;

INSERT INTO account_entries(id,tenant_id,account_id,direction,amount,reference,note,created_at)
SELECT 'show-ae-'||p.id,'demo-erp-tenant-2026','dac-'||lpad((1+(length(p.id)%6))::text,4,'0'),
CASE WHEN p.order_id IS NOT NULL THEN 'in' ELSE 'out' END,p.amount,p.id,
'دریافت یا پرداخت نمونه و غیرواقعی',p.created_at
FROM payments p WHERE p.tenant_id='demo-erp-tenant-2026' AND p.id LIKE 'show-pay-%'
ON CONFLICT (id) DO NOTHING;

INSERT INTO invoices(id,tenant_id,order_id,number,customer_name,customer_address,subtotal,discount,total,issuer_id,created_at)
SELECT 'show-inv-'||substring(s.id from 9),'demo-erp-tenant-2026',s.id,
'SHOW-INV-'||substring(s.id from 9),c.name,c.address,
s.total+s.discount,s.discount,s.total,'demo-erp-user-public',s.created_at+INTERVAL '2 hours'
FROM sales_orders s JOIN customers c ON c.id=s.customer_id
WHERE s.tenant_id='demo-erp-tenant-2026' AND s.id LIKE 'show-so-%' AND s.status in ('fulfilled','confirmed')
ON CONFLICT (id) DO NOTHING;

INSERT INTO invoice_lines(id,tenant_id,invoice_id,variant_id,sku_snapshot,name_snapshot,quantity,price,created_at)
SELECT 'show-invl-'||substring(l.id from 9),'demo-erp-tenant-2026',
'show-inv-'||substring(l.order_id from 9),l.variant_id,v.sku,v.name,l.quantity,l.price,l.created_at
FROM sales_lines l JOIN sales_orders s ON s.id=l.order_id JOIN variants v ON v.id=l.variant_id
WHERE s.tenant_id='demo-erp-tenant-2026' AND s.id LIKE 'show-so-%' AND s.status IN ('fulfilled','confirmed')
ON CONFLICT (id) DO NOTHING;

INSERT INTO shipments(id,tenant_id,order_id,carrier,tracking_number,status,address,created_at)
SELECT 'show-sh-'||i,'demo-erp-tenant-2026','show-so-'||lpad(i::text,4,'0'),
(ARRAY['پست پیشتاز','تیپاکس','پیک اختصاصی'])[1+(i%3)],
'SHOW-TRACK-'||lpad(i::text,8,'0'),
(ARRAY['delivered','shipped','pending'])[1+(i%3)],
'نشانی ساختگی برای نمایش وضعیت ارسال',NOW()-(i%90)*INTERVAL '1 day'
FROM generate_series(144,460,4) i ON CONFLICT (id) DO NOTHING;

INSERT INTO returns(id,tenant_id,order_id,purchase_id,variant_id,warehouse_id,quantity,amount,direction,restock,created_at)
SELECT 'show-rt-'||i,'demo-erp-tenant-2026',
'show-so-'||lpad(i::text,4,'0'),NULL,
'show-v-'||lpad((193+(((i-141)*2)%640))::text,5,'0'),
'dw-'||lpad((1+(i%6))::text,4,'0'),
1,450000+(193+(((i-141)*2)%640))*3200,
'sale',true,NOW()-(i%30)*INTERVAL '1 day'
FROM generate_series(144,456,8) i ON CONFLICT (id) DO NOTHING;

INSERT INTO transfers(id,tenant_id,source_id,destination_id,variant_id,quantity,status,actor_id,created_at)
SELECT 'show-tr-'||i,'demo-erp-tenant-2026',
'dw-'||lpad((1+(i%6))::text,4,'0'),
'dw-'||lpad((1+((i+1)%6))::text,4,'0'),
'show-v-'||lpad((193+((i-71)%640))::text,5,'0'),1+(i%3),
(ARRAY['draft','shipped','received'])[1+(i%3)],'demo-erp-user-public',
NOW()-(i%48)*INTERVAL '1 day'
FROM generate_series(71,220) i ON CONFLICT (id) DO NOTHING;

INSERT INTO notifications(id,tenant_id,title,body,category,read,created_at)
SELECT 'show-notif-'||i,'demo-erp-tenant-2026',
(ARRAY['سفارش اینترنتی جدید','کالای رو به اتمام','پرداخت ثبت شد','خرید تأمین‌کننده','مرجوعی مشتری','انبارگردانی','تغییر قیمت کالا','اطلاعیه ارسال'])[1+(i%8)],
'رویداد ساختگی شماره '||i||' برای نمایش امکانات اعلان‌های فروشگاهی. عملیات واقعی انجام نشده است.',
(ARRAY['sale','stock','payment','purchase','finance','stock','report','shipping'])[1+(i%8)],
i%3=0,NOW()-(i%40)*INTERVAL '1 day'-(i%12)*INTERVAL '1 hour'
FROM generate_series(91,340) i ON CONFLICT (id) DO NOTHING;

INSERT INTO audit_logs(id,tenant_id,actor_id,action,entity,entity_id,details,created_at)
SELECT 'show-audit-'||i,'demo-erp-tenant-2026','demo-erp-user-public',
(ARRAY['create','update','confirm','fulfill','receive','adjust_stock','settle_return','issue_invoice'])[1+(i%8)],
(ARRAY['sales','products','transfers','warehouses','purchases','stocks','returns','invoices'])[1+(i%8)],
NULL,json_build_object('demo',true,'number',i),
NOW()-(i%45)*INTERVAL '1 day'-(i%11)*INTERVAL '1 hour'
FROM generate_series(111,410) i ON CONFLICT (id) DO NOTHING;

INSERT INTO price_items(id,tenant_id,list_id,variant_id,price,created_at)
SELECT 'show-price-'||l||'-'||i,'demo-erp-tenant-2026',
'dpl-'||lpad(l::text,4,'0'),'show-v-'||lpad(i::text,5,'0'),
(450000+i*3200)-(l*11000),NOW()-INTERVAL '17 days'
FROM generate_series(1,6) l CROSS JOIN generate_series(193,832) i
ON CONFLICT (id) DO NOTHING;
COMMIT;

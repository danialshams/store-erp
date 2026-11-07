-- Synthetic, isolated and idempotent public showroom. NEVER seed actual tenants.
-- Rerunning inserts missing examples without deleting or changing existing records.
BEGIN;
INSERT INTO tenants (id,name,phone,address,currency,created_at) VALUES ('demo-erp-tenant-2026','فروشگاه نمونه آبان | ERP نمایشی',NULL,'آدرس ساختگی — فقط برای مشاهده نمونه','TOMAN',NOW()-INTERVAL '180 days') ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id,name,email,password_hash,active,created_at) VALUES ('demo-erp-user-public','بازدیدکننده عمومی','demo-host@example.invalid','disabled-demo-credentials',true,NOW()-INTERVAL '180 days') ON CONFLICT (id) DO NOTHING;

INSERT INTO members (id,tenant_id,user_id,role,active,created_at) VALUES ('demo-member-public','demo-erp-tenant-2026','demo-erp-user-public','owner',true,NOW()-INTERVAL '180 days') ON CONFLICT (id) DO NOTHING;

INSERT INTO users(id,name,email,password_hash,active,created_at)
SELECT 'du-'||lpad(i::text,4,'0'),(ARRAY['نازنین صادقی','آرمان یزدی','مهسا راد','محمد پارسا','نگار احمدی','سپهر محمودی','سارا زمانی','بردیا نوری','یگانه کریمی','پرهام توکلی']) [i],
'demo-colleague-'||i||'@example.invalid','disabled-demo-credentials',true,NOW()-i*INTERVAL '9 days'
FROM generate_series(1,10) i ON CONFLICT (id) DO NOTHING;

INSERT INTO members(id,tenant_id,user_id,role,active,created_at)
SELECT 'dm-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026','du-'||lpad(i::text,4,'0'),
(ARRAY['admin','inventory_manager','sales','accountant','viewer']) [1+((i-1)%5)],true,NOW()-i*INTERVAL '7 days'
FROM generate_series(1,10) i ON CONFLICT (id) DO NOTHING;

INSERT INTO categories(id,tenant_id,name,parent_id,created_at)
SELECT 'dc-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['موبایل و تبلت','لپ‌تاپ و رایانه','هدفون و هندزفری','ساعت هوشمند','لوازم جانبی موبایل','تجهیزات گیمینگ','دوربین و عکاسی','لوازم خانگی','آرایشی و بهداشتی','مد و پوشاک','کفش','کیف و اکسسوری','کتاب و لوازم تحریر','صوتی و تصویری','تجهیزات شبکه','مراقبت شخصی'])[i],
NULL,NOW()-i*INTERVAL '7 days'
FROM generate_series(1,16) i ON CONFLICT (id) DO NOTHING;

INSERT INTO products(id,tenant_id,name,category_id,description,image_url,active,archived,created_at)
SELECT 'dp-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['گوشی هوشمند','لپ‌تاپ حرفه‌ای','هدفون بی‌سیم','ساعت هوشمند','قاب محافظ','کیبورد مکانیکی','دوربین دیجیتال','قهوه‌ساز','عطر زنانه','پیراهن کتان','کفش روزمره','کوله‌پشتی','دفتر برنامه‌ریزی','اسپیکر بلوتوث','روتر وای‌فای','ماشین اصلاح'])[1+((i-1)%16)]||' مدل '||(ARRAY['Nova','Studio','Pro','Plus','Air','Classic']) [1+((i-1)/16)]||' - '||(ARRAY['مشکی','سفید','نقره‌ای','آبی'])[1+((i-1)%4)],
'dc-'||lpad((1+((i-1)%16))::text,4,'0'),
'توضیحات نمونه محصول شامل مشخصات فنی، خدمات پس از فروش و ویژگی‌های انتخاب. تمام اطلاعات و قیمت‌ها ساختگی هستند.',
NULL,true,false,NOW()-(i%85)*INTERVAL '1 day'
FROM generate_series(1,96) i ON CONFLICT (id) DO NOTHING;

INSERT INTO variants(id,tenant_id,product_id,name,sku,barcode,unit,purchase_cost,retail_price,wholesale_price,low_stock,track_batch,track_serial,active,created_at)
SELECT 'dv-'||lpad(i::text,5,'0'),'demo-erp-tenant-2026','dp-'||lpad(((i+1)/2)::text,4,'0'),
CASE WHEN i%2=1 THEN 'نسخه استاندارد' ELSE 'نسخه ویژه' END,
'DEMO-SKU-'||lpad(i::text,5,'0'),'626000'||lpad(i::text,7,'0'),'عدد',
390000 + i*2700,800000+i*5500,710000+i*4500,6+(i%8),
i%7=0,i%13=0,true,NOW()-(i%75)*INTERVAL '1 day'
FROM generate_series(1,192) i ON CONFLICT (id) DO NOTHING;

INSERT INTO warehouses(id,tenant_id,name,code,address,active,created_at)
SELECT 'dw-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['انبار مرکزی تهران','انبار شرق','انبار غرب','انبار فروشگاه حضوری','انبار کالاهای مرجوعی','انبار پشتیبان']) [i],
'WH-'||lpad(i::text,2,'0'),'آدرس آزمایشی انبار شماره '||i,true,NOW()-i*INTERVAL '20 days'
FROM generate_series(1,6) i ON CONFLICT (id) DO NOTHING;

INSERT INTO stocks(id,tenant_id,warehouse_id,variant_id,quantity,reserved,created_at)
SELECT 'dst-'||lpad(w::text,2,'0')||'-'||lpad(v::text,5,'0'),'demo-erp-tenant-2026',
'dw-'||lpad(w::text,4,'0'),'dv-'||lpad(v::text,5,'0'),
CASE WHEN ((v*7+w*11)%17)=0 THEN 2 ELSE 8+((v*7+w*11)%75) END,
CASE WHEN ((v+w)%9)=0 THEN 2 ELSE 0 END,
NOW()-INTERVAL '40 days'
FROM generate_series(1,6) w CROSS JOIN generate_series(1,192) v ON CONFLICT (id) DO NOTHING;

INSERT INTO movements(id,tenant_id,warehouse_id,variant_id,delta,reason,reference_id,note,actor_id,created_at)
SELECT 'dsm-'||lpad(w::text,2,'0')||'-'||lpad(v::text,5,'0'),'demo-erp-tenant-2026',
'dw-'||lpad(w::text,4,'0'),'dv-'||lpad(v::text,5,'0'),
CASE WHEN ((v*7+w*11)%17)=0 THEN 2 ELSE 8+((v*7+w*11)%75) END,
'opening',NULL,'موجودی اولیه نمایشی','demo-erp-user-public',NOW()-INTERVAL '40 days'
FROM generate_series(1,6) w CROSS JOIN generate_series(1,192) v ON CONFLICT (id) DO NOTHING;

INSERT INTO stock_batches(id,tenant_id,warehouse_id,variant_id,lot,expiry_date,quantity,created_at)
SELECT 'dbt-'||lpad(w::text,2,'0')||'-'||lpad(v::text,5,'0'),'demo-erp-tenant-2026',
'dw-'||lpad(w::text,4,'0'),'dv-'||lpad(v::text,5,'0'),
'LOT-2026-'||lpad(v::text,5,'0'),
CURRENT_DATE+((v%23)+1)*INTERVAL '20 days',
CASE WHEN ((v*7+w*11)%17)=0 THEN 2 ELSE 8+((v*7+w*11)%75) END,
NOW()-INTERVAL '36 days'
FROM generate_series(1,2) w CROSS JOIN generate_series(1,192) v ON CONFLICT (id) DO NOTHING;

INSERT INTO suppliers(id,tenant_id,name,phone,email,address,notes,created_at)
SELECT 'dsu-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['توزیع کالای سپهر','بازرگانی دماوند','پخش آریانا','توسعه تجارت نوین','راهکارهای کیان','تأمین پارسیان'])[1+((i-1)%6)]||' - شعبه '||i,
NULL,'supplier-'||i||'@example.invalid','نشانی ساختگی تأمین‌کننده','تأمین‌کننده نمونه برای نمایش مدیریت خرید',NOW()-i*INTERVAL '5 days'
FROM generate_series(1,24) i ON CONFLICT (id) DO NOTHING;

INSERT INTO customers(id,tenant_id,name,phone,email,address,group_name,credit_limit,created_at)
SELECT 'dcu-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['مریم','علی','مهتاب','رضا','سارا','آرین','الناز','نوید','بهار','کاوه'])[1+((i-1)%10)]||' '||(ARRAY['شریفی','کریمی','رحمانی','زمانی','حسینی','پارسا','راد','صالحی','نوری','محمدی'])[1+(((i-1)/10)%10)],
NULL,'customer-'||i||'@example.invalid','شهر نمونه - نشانی ساختگی',
(ARRAY['عادی','وفادار','عمده','ویژه'])[1+((i-1)%4)],(i%8)*2500000,
NOW()-(i%100)*INTERVAL '1 day' FROM generate_series(1,125) i ON CONFLICT (id) DO NOTHING;

INSERT INTO cash_accounts(id,tenant_id,name,type,opening_balance,created_at)
SELECT 'dac-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['صندوق شعبه مرکزی','حساب بانکی اصلی','حساب تنخواه','صندوق فروشگاه','حساب دریافت آنلاین','حساب ذخیره'])[i],
CASE WHEN i IN (2,5,6) THEN 'bank' ELSE 'cash' END,
i*13000000,NOW()-INTERVAL '160 days'
FROM generate_series(1,6) i ON CONFLICT (id) DO NOTHING;

INSERT INTO price_lists(id,tenant_id,name,group_name,active,created_at)
SELECT 'dpl-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['قیمت عمومی','طرح مشتریان وفادار','خرید عمده','همکاران تجاری','کمپین فصل','مشتریان ویژه'])[i],
(ARRAY['عادی','وفادار','عمده','همکار','کمپین','ویژه'])[i],true,NOW()-i*INTERVAL '8 days'
FROM generate_series(1,6) i ON CONFLICT (id) DO NOTHING;

INSERT INTO price_items(id,tenant_id,list_id,variant_id,price,created_at)
SELECT 'dpi-'||lpad(l::text,2,'0')||'-'||lpad(v::text,5,'0'),'demo-erp-tenant-2026',
'dpl-'||lpad(l::text,4,'0'),'dv-'||lpad(v::text,5,'0'),
(800000+v*5500)-(l*10000),NOW()-INTERVAL '12 days'
FROM generate_series(1,6) l CROSS JOIN generate_series(1,40) v ON CONFLICT (id) DO NOTHING;

INSERT INTO tax_rates(id,tenant_id,name,percentage,created_at)
SELECT 'dtx-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['بدون مالیات','نرخ نمونه ۹ درصد','نرخ نمونه ۱۰ درصد','نرخ نمونه ۵ درصد'])[i],
(ARRAY[0,9,10,5])[i],NOW()-INTERVAL '25 days'
FROM generate_series(1,4) i ON CONFLICT (id) DO NOTHING;

WITH source AS (
 SELECT i,1+((i*3)%192) AS a,1+((i*3+1)%192) AS b,1+(i%4) AS qa,1+(i%2) AS qb,
 (i%3)*20000 AS discount FROM generate_series(1,140) i
)
INSERT INTO sales_orders(id,tenant_id,customer_id,warehouse_id,number,channel,status,total,paid,discount,created_at)
SELECT 'ds-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026','dcu-'||lpad((1+((i*7)%125))::text,4,'0'),
'dw-'||lpad((1+(i%5))::text,4,'0'),'DEMO-SO-'||lpad(i::text,5,'0'),
(ARRAY['retail','wholesale','online','pos'])[1+(i%4)],
(ARRAY['fulfilled','confirmed','draft','cancelled'])[1+(i%4)],
((800000+a*5500)*qa+(800000+b*5500)*qb-discount),
CASE WHEN i%4=3 THEN 0 WHEN i%5=0 THEN ((800000+a*5500)*qa+(800000+b*5500)*qb-discount)
WHEN i%5=1 THEN ((800000+a*5500)*qa+(800000+b*5500)*qb-discount)/2 ELSE 0 END,
discount,
NOW()-(i%75)*INTERVAL '1 day'-(i%10)*INTERVAL '2 hours'
FROM source ON CONFLICT (id) DO NOTHING;

WITH series AS (SELECT i,1+((i*3)%192) AS a,1+((i*3+1)%192) AS b,1+(i%4) AS qa,1+(i%2) AS qb FROM generate_series(1,140) i)
INSERT INTO sales_lines(id,tenant_id,order_id,variant_id,quantity,returned,price,cost_snapshot,created_at)
SELECT 'dsl-'||lpad(i::text,4,'0')||'-1','demo-erp-tenant-2026','ds-'||lpad(i::text,4,'0'),
'dv-'||lpad(a::text,5,'0'),qa,CASE WHEN i%20=0 THEN 1 ELSE 0 END,800000+a*5500,390000+a*2700,NOW()-(i%75)*INTERVAL '1 day'
FROM series
UNION ALL SELECT 'dsl-'||lpad(i::text,4,'0')||'-2','demo-erp-tenant-2026','ds-'||lpad(i::text,4,'0'),
'dv-'||lpad(b::text,5,'0'),qb,0,800000+b*5500,390000+b*2700,NOW()-(i%75)*INTERVAL '1 day' FROM series
ON CONFLICT (id) DO NOTHING;

INSERT INTO purchase_orders(id,tenant_id,supplier_id,warehouse_id,number,status,total,paid,created_at)
SELECT 'dpo-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
'dsu-'||lpad((1+((i*3)%24))::text,4,'0'),'dw-'||lpad((1+(i%6))::text,4,'0'),
'DEMO-PO-'||lpad(i::text,5,'0'),
(ARRAY['received','partial','draft','received'])[1+(i%4)],
(2+(i%4))*(390000+(1+((i*2)%192))*2700)+(1+(i%3))*(390000+(1+((i*2+1)%192))*2700),
CASE WHEN i%4=2 THEN 0 WHEN i%3=0 THEN
(2+(i%4))*(390000+(1+((i*2)%192))*2700)+(1+(i%3))*(390000+(1+((i*2+1)%192))*2700)
WHEN i%3=1 THEN ((2+(i%4))*(390000+(1+((i*2)%192))*2700)+(1+(i%3))*(390000+(1+((i*2+1)%192))*2700))/2 ELSE 0 END,
NOW()-(i%85)*INTERVAL '1 day'
FROM generate_series(1,90) i ON CONFLICT (id) DO NOTHING;

WITH series AS (SELECT i,1+((i*2)%192) AS a,1+((i*2+1)%192) AS b,2+(i%4) AS qa,1+(i%3) AS qb FROM generate_series(1,90) i)
INSERT INTO purchase_lines(id,tenant_id,order_id,variant_id,quantity,received,cost,created_at)
SELECT 'dpol-'||lpad(i::text,4,'0')||'-1','demo-erp-tenant-2026','dpo-'||lpad(i::text,4,'0'),
'dv-'||lpad(a::text,5,'0'),qa,CASE WHEN i%4=2 THEN 0 WHEN i%4=1 THEN qa-1 ELSE qa END,
390000+a*2700,NOW()-(i%85)*INTERVAL '1 day' FROM series
UNION ALL
SELECT 'dpol-'||lpad(i::text,4,'0')||'-2','demo-erp-tenant-2026','dpo-'||lpad(i::text,4,'0'),
'dv-'||lpad(b::text,5,'0'),qb,CASE WHEN i%4=2 THEN 0 WHEN i%4=1 THEN 0 ELSE qb END,
390000+b*2700,NOW()-(i%85)*INTERVAL '1 day' FROM series
ON CONFLICT (id) DO NOTHING;

INSERT INTO payments(id,tenant_id,order_id,purchase_id,amount,method,idempotency_key,actor_id,created_at)
SELECT 'dsp-'||substring(id from 4),'demo-erp-tenant-2026',id,NULL,paid,
(ARRAY['cash','card','transfer','online'])[1+((CAST(substring(id from 4) AS INTEGER))%4)],
'demo-sale-payment-'||number,'demo-erp-user-public',created_at+INTERVAL '2 hours'
FROM sales_orders WHERE tenant_id='demo-erp-tenant-2026' AND paid>0
ON CONFLICT (id) DO NOTHING;

INSERT INTO payments(id,tenant_id,order_id,purchase_id,amount,method,idempotency_key,actor_id,created_at)
SELECT 'dpp-'||substring(id from 5),'demo-erp-tenant-2026',NULL,id,paid,
(ARRAY['cash','card','transfer'])[1+((CAST(substring(id from 5) AS INTEGER))%3)],
'demo-purchase-payment-'||number,'demo-erp-user-public',created_at+INTERVAL '1 day'
FROM purchase_orders WHERE tenant_id='demo-erp-tenant-2026' AND paid>0
ON CONFLICT (id) DO NOTHING;

INSERT INTO returns(id,tenant_id,order_id,purchase_id,variant_id,warehouse_id,quantity,amount,direction,restock,created_at)
SELECT 'dsr-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026','ds-'||lpad(i::text,4,'0'),NULL,
'dv-'||lpad((1+((i*3)%192))::text,5,'0'),'dw-'||lpad((1+(i%5))::text,4,'0'),
1,(800000+(1+((i*3)%192))*5500),'sale',true,NOW()-(i%30)*INTERVAL '1 day'
FROM generate_series(20,140,20) i ON CONFLICT (id) DO NOTHING;

INSERT INTO returns(id,tenant_id,order_id,purchase_id,variant_id,warehouse_id,quantity,amount,direction,restock,created_at)
SELECT 'dpr-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',NULL,'dpo-'||lpad(i::text,4,'0'),
'dv-'||lpad((1+((i*2)%192))::text,5,'0'),'dw-'||lpad((1+(i%6))::text,4,'0'),
1,(390000+(1+((i*2)%192))*2700),'purchase',false,NOW()-(i%40)*INTERVAL '1 day'
FROM generate_series(12,84,12) i ON CONFLICT (id) DO NOTHING;

INSERT INTO transfers(id,tenant_id,source_id,destination_id,variant_id,quantity,status,actor_id,created_at)
SELECT 'dtr-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
'dw-'||lpad((1+(i%6))::text,4,'0'),'dw-'||lpad((1+((i+1)%6))::text,4,'0'),
'dv-'||lpad((1+((i*5)%192))::text,5,'0'),1+(i%7),
(ARRAY['draft','shipped','received'])[1+(i%3)],'demo-erp-user-public',
NOW()-(i%45)*INTERVAL '1 day'
FROM generate_series(1,70) i ON CONFLICT (id) DO NOTHING;

INSERT INTO shipments(id,tenant_id,order_id,carrier,tracking_number,status,address,created_at)
SELECT 'dsh-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026','ds-'||lpad(i::text,4,'0'),
(ARRAY['پست پیشتاز','تیپاکس','پیک اختصاصی'])[1+(i%3)],
'DEMO-TRACK-'||lpad(i::text,8,'0'),(ARRAY['delivered','shipped','pending'])[1+(i%3)],
'نشانی نمونه مشتری — غیرواقعی',NOW()-(i%50)*INTERVAL '1 day'
FROM generate_series(4,140,4) i ON CONFLICT (id) DO NOTHING;

INSERT INTO invoices(id,tenant_id,order_id,number,customer_name,customer_address,subtotal,discount,total,issuer_id,created_at)
SELECT 'din-'||substring(o.id from 4),'demo-erp-tenant-2026',o.id,
'DEMO-INV-'||substring(o.id from 4),
c.name,c.address,o.total+o.discount,o.discount,o.total,'demo-erp-user-public',o.created_at+INTERVAL '3 hours'
FROM sales_orders o JOIN customers c ON c.id=o.customer_id
WHERE o.tenant_id='demo-erp-tenant-2026' AND o.status IN ('confirmed','fulfilled')
ON CONFLICT (id) DO NOTHING;

INSERT INTO invoice_lines(id,tenant_id,invoice_id,variant_id,sku_snapshot,name_snapshot,quantity,price,created_at)
SELECT 'dinl-'||substring(l.id from 5),'demo-erp-tenant-2026',
'din-'||substring(l.order_id from 4),l.variant_id,v.sku,v.name,l.quantity,l.price,l.created_at
FROM sales_lines l JOIN sales_orders o ON o.id=l.order_id JOIN variants v ON v.id=l.variant_id
WHERE o.tenant_id='demo-erp-tenant-2026' AND o.status IN ('confirmed','fulfilled')
ON CONFLICT (id) DO NOTHING;

INSERT INTO account_entries(id,tenant_id,account_id,direction,amount,reference,note,created_at)
SELECT 'dae-'||p.id,'demo-erp-tenant-2026','dac-'||lpad((1+((length(p.id))%6))::text,4,'0'),
CASE WHEN p.order_id IS NOT NULL THEN 'in' ELSE 'out' END,p.amount,p.id,'تراکنش نمایشی سفارش',p.created_at
FROM payments p WHERE p.tenant_id='demo-erp-tenant-2026' ON CONFLICT (id) DO NOTHING;

INSERT INTO notifications(id,tenant_id,title,body,category,read,created_at)
SELECT 'dn-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',
(ARRAY['سفارش جدید','موجودی کم','پرداخت ثبت شد','دریافت خرید','مرجوعی ثبت شد','هشدار انبار','گزارش مالی آماده است','ارسال کالا'])[1+((i-1)%8)],
'اعلان نمایشی شماره '||i||' برای بررسی رویدادهای فروشگاه. اطلاعات نمونه و غیرواقعی است.',
(ARRAY['sale','stock','payment','purchase','finance','stock','report','shipping'])[1+((i-1)%8)],
i%3=0,
NOW()-(i%35)*INTERVAL '1 day'-(i%8)*INTERVAL '1 hour'
FROM generate_series(1,90) i ON CONFLICT (id) DO NOTHING;

INSERT INTO audit_logs(id,tenant_id,actor_id,action,entity,entity_id,details,created_at)
SELECT 'dal-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026',CASE WHEN i%5=0 THEN 'du-'||lpad((1+(i%10))::text,4,'0') ELSE 'demo-erp-user-public' END,
(ARRAY['create','update','confirm','fulfill','receive','adjust_stock','settle_return','issue_invoice'])[1+((i-1)%8)],
(ARRAY['sales','products','transfers','warehouses','purchases','stocks','returns','invoices'])[1+((i-1)%8)],
NULL,json_build_object('sample',true,'ordinal',i),
NOW()-(i%60)*INTERVAL '1 day'-(i%12)*INTERVAL '1 hour'
FROM generate_series(1,110) i ON CONFLICT (id) DO NOTHING;

INSERT INTO sequences(id,tenant_id,key,next_value,created_at)
SELECT 'dseq-'||i,'demo-erp-tenant-2026',
(ARRAY['sales','purchases','invoices','transfers'])[i],
(ARRAY[141,91,71,71])[i],NOW()-INTERVAL '35 days'
FROM generate_series(1,4) i ON CONFLICT (id) DO NOTHING;

INSERT INTO event_keys(id,tenant_id,kind,key,reference_id,created_at)
SELECT 'dek-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026','demo_sale','DEMO-KEY-'||i,
'ds-'||lpad(i::text,4,'0'),NOW()-(i%35)*INTERVAL '1 day'
FROM generate_series(1,40) i ON CONFLICT (id) DO NOTHING;

INSERT INTO invites(id,tenant_id,email,role,token_hash,expires_at,used_at,created_at)
SELECT 'dii-'||lpad(i::text,4,'0'),'demo-erp-tenant-2026','invite-'||i||'@example.invalid',
(ARRAY['viewer','sales','accountant','inventory_manager'])[1+((i-1)%4)],
md5('not-a-real-token-'||i),NOW()-INTERVAL '1 day',NULL,NOW()-INTERVAL '16 days'
FROM generate_series(1,8) i ON CONFLICT (id) DO NOTHING;
COMMIT;

"""Portable Retail ERP: FastAPI / SQLAlchemy / PostgreSQL.

Critical stock mutations are transaction-bound, serialized per stock key,
permission checked and recorded in an append-only ledger.
"""
from __future__ import annotations
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4
import os
import io, csv, hashlib, hmac
from html import escape as html_escape
from fastapi import FastAPI, Request, HTTPException, Depends, Body, Query
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, text, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import Session as DbSession, init_db, engine
from .models import *
from .security import issue_token, parse_token, SECRET, make_password, verify_password, context, authorized, csrf_guard, public_demo_enabled, ROLES, ALL, CATALOG, WAREHOUSE, SALES, PURCHASE, FINANCE

app=FastAPI(title='ERP فروشگاهی',docs_url='/api/docs',openapi_url='/api/openapi.json',redoc_url=None)
PUBLIC=Path(__file__).resolve().parent.parent/'public'
if PUBLIC.is_dir():
    app.mount('/assets', StaticFiles(directory=str(PUBLIC)), name='assets')

@app.middleware('http')
async def safety_middleware(request:Request,call_next):
    if (public_demo_enabled() and request.url.path.startswith('/api/')
            and request.method in ('POST','PUT','PATCH','DELETE')
            and not request.cookies.get('erp_session')):
        # Public visitors can browse an isolated demo but never mutate it.
        # Authenticated customer sessions still use their own tenant and permissions.
        return JSONResponse({'detail':'نسخه نمایشی فقط برای مشاهده است'},status_code=403)
    if request.url.path.startswith('/api/'):
        try:
            csrf_guard(request)
        except HTTPException as exc:
            # Middleware executes outside FastAPI's exception handler; returning
            # a response here avoids a misleading 500 on rejected origins.
            return JSONResponse({'detail': exc.detail}, status_code=exc.status_code)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Cache-Control']='no-store'
    return response

@app.get('/')
def index(): return FileResponse(PUBLIC/'index.html')
@app.get('/app')
def home(): return FileResponse(PUBLIC/'index.html')

# Local development creates SQLite tables. Deployed PostgreSQL must be migrated separately.
if engine.dialect.name=='sqlite' and not os.environ.get('VERCEL'):
    init_db()

def db_session():
    db=DbSession()
    try: yield db
    finally: db.close()

def principal(req:Request,db:Session=Depends(db_session)):
    ctx=context(req,db)
    # A signed user session or the isolated read-only demo identity must be
    # validated BEFORE setting the transaction-local PostgreSQL tenant scope.
    # SET LOCAL avoids leaking the tenant across pooled connections.
    if db.bind.dialect.name=='postgresql':
        db.execute(text("SELECT set_config('erp.tenant_id', :tenant_id, true)"),
                   {'tenant_id':ctx['tenant']})
    return ctx

def tenant_object(db,model,tenant_id,object_id,lock=False):
    q=db.query(model).filter_by(id=object_id,tenant_id=tenant_id)
    if lock:q=q.with_for_update()
    item=q.first()
    if not item:raise HTTPException(404,'رکورد پیدا نشد')
    return item

def as_dict(item):
    return {c.name:(v.isoformat() if isinstance((v:=getattr(item,c.name)),(datetime,date)) else v) for c in item.__table__.columns}

def audit(db,ctx,action,entity,item=None,details=None):
    db.add(Audit(tenant_id=ctx['tenant'],actor_id=ctx['user'].id,action=action,entity=entity,entity_id=item,details=details or {}))

def notification(db,tid,title,body,category):
    db.add(Notification(tenant_id=tid,title=title,body=body,category=category))

# Standard editable chart of accounts; no external accounting provider is needed.
LEDGER_BASE=(
 ('1010','صندوق نقدی','asset'),('1020','بانک و کارتخوان','asset'),
 ('1200','حساب‌های دریافتنی','asset'),('1300','موجودی کالا','asset'),
 ('2000','حساب‌های پرداختنی','liability'),('3000','سرمایه و موجودی افتتاحیه','equity'),
 ('4000','درآمد فروش','revenue'),('4100','برگشت از فروش','revenue'),
 ('5000','بهای تمام‌شده فروش','expense'),('6000','تعدیل و کسری انبار','expense'),
)
def _ensure_ledger(db,tenant):
    if db.bind.dialect.name=='postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'),
                   {'key':'ledger-accounts:'+tenant})
    found={x.code:x for x in db.query(LedgerAccount).filter_by(tenant_id=tenant).all()}
    for code,name,kind in LEDGER_BASE:
        if code not in found:
            item=LedgerAccount(tenant_id=tenant,code=code,name=name,kind=kind,active=True)
            db.add(item);db.flush();found[code]=item
    return found

def _post_journal(db,ctx,source,memo,postings):
    """Post a balanced immutable entry within the calling business transaction."""
    if not postings:return None
    debit=sum(int(dr) for _,dr,_ in postings)
    credit=sum(int(cr) for _,_,cr in postings)
    if debit!=credit or debit<=0 or any(
        type(dr) is not int or type(cr) is not int or
        (dr>0)==(cr>0) or dr<0 or cr<0 for _,dr,cr in postings
    ):
        raise HTTPException(422,'سند حسابداری باید دوطرفه و تراز باشد')
    tenant=ctx['tenant']
    if db.query(Journal).filter_by(tenant_id=tenant,source_key=source).first():
        raise HTTPException(409,'این رویداد قبلاً در دفتر کل ثبت شده است')
    accounts=_ensure_ledger(db,tenant)
    hdr=Journal(tenant_id=tenant,source_key=source,
                number='J-'+uuid4().hex[:22],memo=str(memo)[:1500],
                journal_date=date.today(),actor_id=ctx['user'].id)
    db.add(hdr);db.flush()
    for code,dr,cr in postings:
        acct=accounts.get(code)
        if not acct or not acct.active:raise HTTPException(422,'حساب دفتر کل یافت نشد: '+code)
        db.add(JournalLine(tenant_id=tenant,journal_id=hdr.id,account_id=acct.id,
                           debit=dr,credit=cr))
    db.flush()
    return hdr

def amount(value,name='مبلغ'):
    if type(value) is not int or value < 0 or value > 9_000_000_000_000_000:
        raise HTTPException(422,f'{name} باید عدد صحیح غیرمنفی باشد')
    return value

def positive(value,name='تعداد'):
    if type(value) is not int or value<=0 or value>1_000_000:
        raise HTTPException(422,f'{name} باید عدد صحیح مثبت باشد')
    return value
def positive_amount(value,name='مبلغ'):
    amount(value,name)
    if value==0:raise HTTPException(422,f'{name} باید بیشتر از صفر باشد')
    return value

def require_string(value,label='مقدار',maxlen=200):
    if not isinstance(value,str) or not 0 < len(value.strip()) <= maxlen:
        raise HTTPException(422,f'{label} الزامی است')
    return value.strip()

def _persist_session(db:Session,token:str):
    claim=parse_token(token)
    if not claim or not claim.get('j'):raise HTTPException(500,'صدور نشست امن ناموفق بود')
    db.add(AuthSession(tenant_id=claim['t'],user_id=claim['u'],jti=claim['j'],
                       expires_at=datetime.fromtimestamp(claim['exp'],timezone.utc)))
    db.commit()
    return token

def _throttle_key(email:str,remote:str)->str:
    return hmac.new(SECRET.encode(),(email.lower()+'|'+remote).encode(),
                    hashlib.sha256).hexdigest()

def _login_attempt(db:Session,email:str,remote:str,success:bool=False):
    key=_throttle_key(email,remote)
    if db.bind.dialect.name=='postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'),{'key':'login:'+key})
    now=datetime.now(timezone.utc)
    row=db.query(LoginThrottle).filter_by(key=key).with_for_update().first()
    if not row:
        row=LoginThrottle(key=key,attempts=0,window_start=now)
        db.add(row)
    start=row.window_start
    if start and start.tzinfo is None:start=start.replace(tzinfo=timezone.utc)
    if not start or now-start>timedelta(minutes=10):
        row.window_start=now;row.attempts=0;row.blocked_until=None
    block=row.blocked_until
    if block and block.tzinfo is None:block=block.replace(tzinfo=timezone.utc)
    if block and block>now and not success:
        db.commit()
        raise HTTPException(429,'تلاش‌های ورود بیش از حد است؛ کمی بعد دوباره امتحان کنید')
    if success:
        row.attempts=0;row.blocked_until=None
    else:
        row.attempts+=1
        if row.attempts>=8:row.blocked_until=now+timedelta(minutes=10)
    db.commit()

def secure_cookie(response,token):
    response.set_cookie('erp_session',token,httponly=True,secure=(os.environ.get('COOKIE_SECURE','true' if os.environ.get('VERCEL') else 'false').lower()=='true'),samesite='lax',max_age=604800,path='/')

def account_info(db,ctx):
    return {'name':ctx['user'].name,'email':ctx['user'].email,'user_id':ctx['user'].id,'tenant_id':ctx['tenant'],'tenant':db.get(Tenant,ctx['tenant']).name,'role':ctx['role'],'public_demo':bool(ctx.get('public_demo'))}

@app.post('/api/auth/register')
def register(body:dict=Body(...),db:Session=Depends(db_session)):
    name=require_string(body.get('name'),'نام',120)
    company=require_string(body.get('company'),'نام کسب‌وکار',200)
    email=require_string(body.get('email'),'ایمیل',254).lower()
    password=body.get('password')
    if not isinstance(password,str) or len(password)<12 or len(password)>200:raise HTTPException(422,'رمز عبور باید حداقل ۱۲ نویسه باشد')
    if db.query(User).filter_by(email=email).first():raise HTTPException(409,'ایمیل قبلاً ثبت شده است')
    try:
        user=User(name=name,email=email,password_hash=make_password(password))
        tenant=Tenant(name=company)
        db.add_all([user,tenant]);db.flush()
        if db.bind.dialect.name=='postgresql':
            db.execute(text("SELECT set_config('erp.tenant_id', :tenant_id, true)"),
                       {'tenant_id':tenant.id})
        db.add(Member(tenant_id=tenant.id,user_id=user.id,role='owner'))
        _ensure_ledger(db,tenant.id)
        db.add(Warehouse(tenant_id=tenant.id,name='انبار اصلی',code='MAIN'))
        db.add(CashAccount(tenant_id=tenant.id,name='صندوق اصلی',type='cash'))
        db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'ایمیل تکراری است')
    response=JSONResponse({'ok':True,'tenant_id':tenant.id})
    secure_cookie(response,_persist_session(db,issue_token(user.id,tenant.id)))
    return response

@app.post('/api/auth/login')
def login(body:dict=Body(...),req:Request=None,db:Session=Depends(db_session)):
    email=str(body.get('email','')).lower().strip()
    password=str(body.get('password',''))
    if not email or len(email)>254 or len(password)>300:
        raise HTTPException(422,'اطلاعات ورود نامعتبر است')
    ip=req.client.host if req and req.client else 'unknown'
    _login_attempt(db,email,ip,success=False)
    user=db.query(User).filter_by(email=email,active=True).first()
    # Verify fixed fake digest on unknown user for roughly equal work.
    if not user or not verify_password(password,user.password_hash):
        if not user:verify_password(password,'pbkdf2_sha256$600000$'+'00'*16+'$'+'00'*32)
        raise HTTPException(401,'ایمیل یا رمز عبور اشتباه است')
    membership=db.query(Member).filter_by(user_id=user.id,active=True).first()
    if not membership:raise HTTPException(403,'عضویت فعالی ندارید')
    _login_attempt(db,email,ip,success=True)
    response=JSONResponse({'ok':True})
    secure_cookie(response,_persist_session(db,issue_token(user.id,membership.tenant_id)))
    return response

@app.post('/api/auth/logout')
def logout(req:Request,db:Session=Depends(db_session)):
    claim=parse_token(req.cookies.get('erp_session',''))
    if claim and claim.get('j'):
        item=db.query(AuthSession).filter_by(jti=claim['j'],user_id=claim['u'],
                                          tenant_id=claim['t']).with_for_update().first()
        if item:
            item.revoked_at=datetime.now(timezone.utc)
            db.commit()
    response=JSONResponse({'ok':True})
    response.delete_cookie('erp_session',path='/')
    return response

@app.get('/api/auth/me')
def me(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    return account_info(db,ctx)

# Generic resources are direct editable reference data only; orders, balances and ledger
# are expressly absent from the generic mutation map.
SPEC={
 'categories':(Category,CATALOG,['name','parent_id'],['name']),
 'products':(Product,CATALOG,['name','category_id','description','image_url','active'],['name','description']),
 'variants':(Variant,CATALOG,['product_id','name','sku','barcode','unit','purchase_cost','retail_price','wholesale_price','low_stock','track_batch','track_serial','active'],['sku','name','barcode']),
 'warehouses':(Warehouse,WAREHOUSE,['name','code','address','active'],['name','code']),
 'suppliers':(Supplier,PURCHASE,['name','phone','email','address','notes'],['name','phone']),
 'customers':(Customer,SALES|FINANCE,['name','phone','email','address','group_name','credit_limit'],['name','phone']),
 'price-lists':(PriceList,SALES,['name','group_name','active'],['name']),
 'price-items':(PriceItem,SALES,['list_id','variant_id','price'],[]),
 'cash-accounts':(CashAccount,FINANCE,['name','type','opening_balance'],['name']),
 'tax-rates':(Tax,FINANCE,['name','percentage'],['name']),
 'shipments':(Shipment,SALES,['order_id','carrier','tracking_number','status','address'],['tracking_number','carrier']),
}
READABLE={
 **{k:(v[0],ALL,v[3]) for k,v in SPEC.items()},
 'stocks':(Stock,ALL,[]),'movements':(Movement,ALL,['reason']),
 'batches':(StockBatch,ALL,['lot']), 'serials':(SerialItem,ALL,['serial','status']),
 'lot-movements':(LotMovement,ALL,['reason']), 'transfers':(Transfer,ALL,['status']),
 'purchases':(PurchaseOrder,ALL,['number','status']),
 'purchase-lines':(PurchaseLine,ALL,[]),'sales':(SalesOrder,ALL,['number','status']),
 'sales-lines':(SalesLine,ALL,[]),'fulfillments':(Fulfillment,ALL,['number','status']), 'payments':(Payment,FINANCE|SALES,['method']),
 'returns':(Return,ALL,['direction']), 'account-entries':(AccountEntry,FINANCE,[]),
 'notifications':(Notification,ALL,['title']), 'audit':(Audit,{'owner','admin'},['action','entity'])
}
REFS={'parent_id':Category,'category_id':Category,'product_id':Product,'warehouse_id':Warehouse,
      'supplier_id':Supplier,'customer_id':Customer,'variant_id':Variant,'list_id':PriceList,'order_id':SalesOrder,'parent_id':Category}
FIELDS_NONNEGATIVE={'purchase_cost','retail_price','wholesale_price','low_stock','credit_limit','price','opening_balance','percentage'}

def checked_fields(db,ctx,model,fields,body):
    if not isinstance(body,dict) or not body:raise HTTPException(422,'اطلاعات موردنیاز ارسال نشده است')
    if set(body)-set(fields):raise HTTPException(422,'فیلد نامعتبر: '+','.join(set(body)-set(fields)))
    for k,v in body.items():
        if k in REFS and v is not None:
            tenant_object(db,REFS[k],ctx['tenant'],v)
        if k in FIELDS_NONNEGATIVE: amount(v,k)
        if k=='percentage' and v>100:raise HTTPException(422,'درصد نامعتبر')
        if k in {'name','sku','code'}:require_string(v,k,250)
        if k=='image_url' and v is not None and (not isinstance(v,str) or len(v)>2048 or not v.startswith('https://')):
            raise HTTPException(422,'آدرس تصویر باید HTTPS باشد')
        if k=='status' and model is Shipment and v not in ['pending','shipped','delivered','returned']:
            raise HTTPException(422,'وضعیت نامعتبر')
    return body

@app.get('/api/data/{resource}')
def list_resource(resource:str,search:str='',page:int=Query(1,ge=1,le=100000),limit:int=Query(30,ge=1,le=100),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    if resource not in READABLE:raise HTTPException(404,'بخش موجود نیست')
    model,roles,search_cols=READABLE[resource]
    authorized(ctx,roles)
    q=db.query(model).filter_by(tenant_id=ctx['tenant'])
    if resource=='products': q=q.filter_by(archived=False)
    if search and search_cols:
        q=q.filter(or_(*[getattr(model,col).ilike(f'%{search[:100]}%') for col in search_cols]))
    total=q.count()
    records=q.order_by(model.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {'items':[as_dict(x) for x in records],'total':total,'page':page,'limit':limit}

@app.post('/api/data/{resource}')
def create_resource(resource:str,body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    if resource not in SPEC: raise HTTPException(405,'این عملیات فقط از مسیر اختصاصی مجاز است')
    model,roles,fields,_=SPEC[resource]
    authorized(ctx,roles)
    vals=checked_fields(db,ctx,model,fields,body)
    if resource=='shipments':
        linked=tenant_object(db,SalesOrder,ctx['tenant'],vals.get('order_id'))
        if linked.status not in ('fulfilled','partial'):raise HTTPException(409,'ارسال فقط برای سفارش دارای تحویل قابل ثبت است')
    try:
        obj=model(tenant_id=ctx['tenant'],**vals)
        db.add(obj);db.flush()
        audit(db,ctx,'create',resource,obj.id)
        db.commit()
        return as_dict(obj)
    except IntegrityError:db.rollback();raise HTTPException(409,'مقادیر تکراری یا ارتباط نامعتبر است')

@app.patch('/api/data/{resource}/{item_id}')
def update_resource(resource:str,item_id:str,body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    if resource not in SPEC:raise HTTPException(405,'ویرایش از این مسیر مجاز نیست')
    model,roles,fields,_=SPEC[resource]
    authorized(ctx,roles)
    obj=tenant_object(db,model,ctx['tenant'],item_id,lock=True)
    vals=checked_fields(db,ctx,model,fields,body)
    if resource=='products' and 'archived' in vals:raise HTTPException(422,'آرشیو از مسیر حذف انجام می‌شود')
    if resource=='shipments' and 'order_id' in vals:
        linked=tenant_object(db,SalesOrder,ctx['tenant'],vals['order_id'])
        if linked.status!='fulfilled':raise HTTPException(409,'سفارش قابل ارسال نیست')
    if resource=='shipments' and obj.status=='delivered' and 'status' in vals and vals['status']!='delivered':
        raise HTTPException(409,'ارسال تحویل‌شده قابل بازگشت نیست')
    for k,v in vals.items():setattr(obj,k,v)
    audit(db,ctx,'update',resource,obj.id)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'مقادیر نامعتبر یا تکراری')
    return as_dict(obj)

@app.delete('/api/data/{resource}/{item_id}')
def delete_resource(resource:str,item_id:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    if resource not in SPEC:raise HTTPException(405,'حذف از این مسیر مجاز نیست')
    model,roles,_,_=SPEC[resource]
    authorized(ctx,roles)
    obj=tenant_object(db,model,ctx['tenant'],item_id,lock=True)
    if resource=='products':
        obj.archived=True;obj.active=False
    elif resource=='variants':
        obj.active=False
    else:
        db.delete(obj)
    audit(db,ctx,'archive' if resource in ('products','variants') else 'delete',resource,item_id)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'این رکورد در اسناد دیگر استفاده شده و امکان حذف آن نیست')
    return {'ok':True}

# Inventory changes: only this function writes stocks and movements.
# Per-key transaction advisory lock prevents races even when no balance row exists yet.
def _record_lot_change(db,ctx,batch,warehouse_id,variant_id,qty,reason,ref):
    if qty==0:return
    batch.quantity+=qty
    if batch.quantity<0:raise HTTPException(409,'موجودی بچ کافی نیست')
    db.add(LotMovement(tenant_id=ctx['tenant'],warehouse_id=warehouse_id,
                       variant_id=variant_id,batch_id=batch.id,delta=qty,
                       reason=reason,reference_id=ref))

def _add_lot(db,ctx,warehouse_id,variant_id,qty,lot,expiry_date,reason,ref):
    lot=require_string(lot,'شماره بچ',100)
    expiry=None
    if expiry_date:
        try:expiry=date.fromisoformat(expiry_date) if isinstance(expiry_date,str) else expiry_date
        except (ValueError,TypeError):raise HTTPException(422,'تاریخ انقضا نامعتبر است')
        if not isinstance(expiry,date):raise HTTPException(422,'تاریخ انقضا نامعتبر است')
    row=db.query(StockBatch).filter_by(tenant_id=ctx['tenant'],warehouse_id=warehouse_id,
                  variant_id=variant_id,lot=lot).with_for_update().first()
    if row:
        if row.expiry_date!=expiry:raise HTTPException(409,'تاریخ انقضای بچ با رکورد قبلی متفاوت است')
    else:
        row=StockBatch(tenant_id=ctx['tenant'],warehouse_id=warehouse_id,
                       variant_id=variant_id,lot=lot,expiry_date=expiry,quantity=0)
        db.add(row);db.flush()
    _record_lot_change(db,ctx,row,warehouse_id,variant_id,qty,reason,ref)

def _take_lots(db,ctx,warehouse_id,variant_id,qty,reason,ref):
    rows=db.query(StockBatch).filter_by(tenant_id=ctx['tenant'],warehouse_id=warehouse_id,
                  variant_id=variant_id).with_for_update().all()
    candidates=[x for x in rows if x.quantity>0 and
                (reason!='sale_fulfill' or x.expiry_date is None or x.expiry_date>=date.today())]
    candidates.sort(key=lambda x:(x.expiry_date is None,x.expiry_date or date.max,x.created_at))
    left=qty
    for row in candidates:
        count=min(left,row.quantity)
        if count:
            _record_lot_change(db,ctx,row,warehouse_id,variant_id,-count,reason,ref)
            left-=count
        if left==0:break
    if left:raise HTTPException(409,'بچ با موجودی کافی و تاریخ معتبر برای خروج پیدا نشد')

def _restore_lots(db,ctx,warehouse_id,variant_id,qty,reason,ref):
    if not ref:raise HTTPException(422,'مرجع گردش بچ نامعتبر')
    source_reason='transfer_ship' if reason=='transfer_receive' else 'sale_fulfill'
    previous=db.query(LotMovement).filter_by(tenant_id=ctx['tenant'],variant_id=variant_id,
                        reference_id=ref,reason=source_reason).all()
    previous=[m for m in previous if m.delta<0]
    already={}
    if reason=='customer_return':
        for m in db.query(LotMovement).filter_by(tenant_id=ctx['tenant'],variant_id=variant_id,
                                                 reference_id=ref,reason='customer_return').all():
            already[m.batch_id]=already.get(m.batch_id,0)+m.delta
    left=qty
    for m in previous:
        original=tenant_object(db,StockBatch,ctx['tenant'],m.batch_id)
        eligible=-m.delta-(already.get(m.batch_id,0) if reason=='customer_return' else 0)
        count=min(left,max(0,eligible))
        if count:
            _add_lot(db,ctx,warehouse_id,variant_id,count,original.lot,
                     original.expiry_date,reason,ref)
            already[m.batch_id]=already.get(m.batch_id,0)+count
            left-=count
        if left==0:break
    if left:raise HTTPException(409,'بچ‌های مربوط به سند برای بازگشت کامل پیدا نشد')

def _trace_serials(db,ctx,warehouse_id,variant_id,delta,reason,ref,serials,reserved_after):
    tid=ctx['tenant']
    if abs(delta)>100:raise HTTPException(422,'گردش کالا با شماره سریال در هر عملیات حداکثر ۱۰۰ عدد است')
    if delta>0:
        if reason=='transfer_receive':
            rows=db.query(SerialItem).filter_by(tenant_id=tid,variant_id=variant_id,
                    reference_id=ref,status='in_transit').with_for_update().all()
            if len(rows)!=delta:raise HTTPException(409,'سریال‌های در مسیر با تعداد حواله تطابق ندارند')
            for x in rows:x.warehouse_id=warehouse_id;x.status='in_stock';x.reference_id=None
        elif reason=='customer_return':
            if not isinstance(serials,list) or len(serials)!=delta or not all(isinstance(x,str) for x in serials) or len(set(serials))!=delta:
                raise HTTPException(422,'شماره سریال اقلام برگشتی باید دقیقاً مشخص شود')
            rows=db.query(SerialItem).filter(SerialItem.tenant_id==tid,
                  SerialItem.variant_id==variant_id,SerialItem.serial.in_(serials)).with_for_update().all()
            if len(rows)!=delta or any(x.status!='sold' or x.reference_id!=ref for x in rows):
                raise HTTPException(409,'سریال برگشتی با فروش اصلی مطابقت ندارد')
            for x in rows:x.warehouse_id=warehouse_id;x.status='in_stock';x.reference_id=None
        else:
            if not isinstance(serials,list) or len(serials)!=delta or not all(isinstance(x,str) for x in serials) or len(set(serials))!=delta:
                raise HTTPException(422,'فهرست سریال‌ها باید دقیقاً برابر تعداد دریافتی باشد')
            if db.query(SerialItem).filter(SerialItem.tenant_id==tid,
                  SerialItem.serial.in_(serials)).first():
                raise HTTPException(409,'شماره سریال قبلاً ثبت شده است')
            for serial in serials:
                require_string(serial,'شماره سریال',150)
                db.add(SerialItem(tenant_id=tid,warehouse_id=warehouse_id,
                                  variant_id=variant_id,serial=serial,status='in_stock'))
            try:db.flush()
            except IntegrityError:
                db.rollback()
                raise HTTPException(409,'شماره سریال تکراری است')
    elif delta<0:
        rows=db.query(SerialItem).filter_by(tenant_id=tid,warehouse_id=warehouse_id,
                   variant_id=variant_id,status='in_stock').order_by(
                       SerialItem.created_at.asc()).with_for_update().limit(-delta).all()
        if len(rows)!=-delta:raise HTTPException(409,'شماره سریال موجود برای خروج کافی نیست')
        to_status={'sale_fulfill':'sold','transfer_ship':'in_transit',
                   'supplier_return':'supplier_returned',
                   'loss':'retired','damage':'retired'}.get(reason,'retired')
        for x in rows:x.status=to_status;x.reference_id=ref
    elif reserved_after>0:
        count=db.query(SerialItem).filter_by(tenant_id=tid,warehouse_id=warehouse_id,
                    variant_id=variant_id,status='in_stock').count()
        if count<reserved_after:raise HTTPException(409,'تعداد سریال‌های موجود کمتر از رزرو است')

def _trace_batches(db,ctx,warehouse_id,variant_id,delta,reason,ref,
                   reserved_after,lot,expiry_date):
    tid=ctx['tenant']
    if delta>0:
        if reason in ('transfer_receive','customer_return'):
            _restore_lots(db,ctx,warehouse_id,variant_id,delta,reason,ref)
        else:
            _add_lot(db,ctx,warehouse_id,variant_id,delta,lot,expiry_date,reason,ref)
    elif delta<0:
        _take_lots(db,ctx,warehouse_id,variant_id,-delta,reason,ref)
    elif reserved_after>0:
        total=sum(b.quantity for b in db.query(StockBatch).filter_by(
               tenant_id=tid,warehouse_id=warehouse_id,variant_id=variant_id).all()
               if b.expiry_date is None or b.expiry_date>=date.today())
        if total<reserved_after:raise HTTPException(409,'موجودی بچ معتبر برای رزرو کافی نیست')


def _stock(db:Session,ctx,warehouse_id,variant_id,delta,reason,ref=None,note=None,release_reserved=0,reserve=0,lot=None,expiry_date=None,serials=None):
    tid=ctx['tenant']
    tenant_object(db,Warehouse,tid,warehouse_id)
    variant=tenant_object(db,Variant,tid,variant_id)
    if db.bind.dialect.name=='postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'),{'key':tid+':'+warehouse_id+':'+variant_id})
    stock=db.query(Stock).filter_by(tenant_id=tid,warehouse_id=warehouse_id,variant_id=variant_id).with_for_update().first()
    if not stock:
        stock=Stock(tenant_id=tid,warehouse_id=warehouse_id,variant_id=variant_id,quantity=0,reserved=0)
        db.add(stock);db.flush()
    next_qty=stock.quantity+delta
    next_reserved=stock.reserved-release_reserved+reserve
    if next_reserved<0 or next_qty<0 or next_qty<next_reserved:raise HTTPException(409,'موجودی آزاد کافی نیست')
    stock.quantity=next_qty;stock.reserved=next_reserved
    if variant.track_batch:
        _trace_batches(db,ctx,warehouse_id,variant_id,delta,reason,ref,
                       next_reserved,lot,expiry_date)
    if variant.track_serial:
        _trace_serials(db,ctx,warehouse_id,variant_id,delta,reason,ref,
                       serials,next_reserved)
    if delta:
        db.add(Movement(tenant_id=tid,warehouse_id=warehouse_id,variant_id=variant_id,delta=delta,reason=reason,reference_id=ref,note=note,actor_id=ctx['user'].id))
    return stock

@app.post('/api/stock/adjust')
def adjust(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,WAREHOUSE)
    delta=body.get('delta')
    if type(delta) is not int or delta==0 or abs(delta)>1_000_000:raise HTTPException(422,'تغییر موجودی نامعتبر')
    reason=require_string(body.get('reason'),'دلیل',100)
    if reason not in ['opening','correction','damage','loss','cycle_count']:raise HTTPException(422,'دلیل معتبر نیست')
    stock=_stock(db,ctx,body.get('warehouse_id'),body.get('variant_id'),delta,reason,note=body.get('note'),lot=body.get('lot'),expiry_date=body.get('expiry_date'),serials=body.get('serials'))
    cost=tenant_object(db,Variant,ctx['tenant'],body.get('variant_id')).purchase_cost
    value=abs(delta*cost)
    if value:
        if delta>0:
            _post_journal(db,ctx,'stock-adjust:'+str(uuid4()),'افزایش موجودی - '+reason,
                          [('1300',value,0),('3000',0,value)])
        else:
            _post_journal(db,ctx,'stock-adjust:'+str(uuid4()),'کاهش موجودی - '+reason,
                          [('6000',value,0),('1300',0,value)])
    audit(db,ctx,'adjust_stock','stocks',stock.id,{'delta':delta,'reason':reason})
    db.commit()
    return as_dict(stock)

@app.get('/api/stock/cycle-sheet')
def cycle_sheet(warehouse_id:str,page:int=Query(1,ge=1,le=100000),
                db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    """Read the quantity snapshot that must match at commit time."""
    authorized(ctx,WAREHOUSE)
    tid=ctx['tenant']
    tenant_object(db,Warehouse,tid,warehouse_id)
    base=db.query(Variant).filter_by(tenant_id=tid,active=True)
    total=base.count()
    variants=base.order_by(Variant.sku).offset((page-1)*100).limit(100).all()
    stocks=(db.query(Stock).filter(Stock.tenant_id==tid,
                                  Stock.warehouse_id==warehouse_id,
                                  Stock.variant_id.in_([v.id for v in variants])).all()) if variants else []
    by_variant={s.variant_id:s for s in stocks}
    return {'warehouse_id':warehouse_id,'page':page,'total':total,
            'items':[{'variant_id':v.id,'sku':v.sku,'name':v.name,
                      'quantity':by_variant[v.id].quantity if v.id in by_variant else 0,
                      'reserved':by_variant[v.id].reserved if v.id in by_variant else 0,
                      'track_batch':v.track_batch,'track_serial':v.track_serial}
                     for v in variants]}

@app.post('/api/stock/cycle-count')
def cycle_count(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    """Count a warehouse snapshot and post any difference to the inventory ledger atomically."""
    authorized(ctx,WAREHOUSE)
    tid=ctx['tenant']
    warehouse_id=body.get('warehouse_id')
    tenant_object(db,Warehouse,tid,warehouse_id)
    key=require_string(body.get('idempotency_key'),'شناسه درخواست',150)
    existing=db.query(EventKey).filter_by(tenant_id=tid,kind='cycle_count',key=key).first()
    if existing:raise HTTPException(409,'این دوره انبارگردانی قبلاً ثبت شده است')
    items=body.get('items')
    if not isinstance(items,list) or not 1<=len(items)<=100:raise HTTPException(422,'بین ۱ تا ۱۰۰ قلم باید وارد شود')
    checked=[];seen=set()
    for item in items:
        if not isinstance(item,dict):raise HTTPException(422,'قلم نامعتبر')
        vid=item.get('variant_id')
        tenant_object(db,Variant,tid,vid)
        if vid in seen:raise HTTPException(422,'ثبت تکراری کالا در انبارگردانی مجاز نیست')
        seen.add(vid)
        counted=item.get('counted');expected=item.get('expected_quantity')
        if type(counted) is not int or counted<0 or counted>1_000_000:
            raise HTTPException(422,'تعداد شمارش‌شده نامعتبر است')
        if type(expected) is not int or expected<0 or expected>1_000_000:
            raise HTTPException(422,'موجودی مبنای شمارش نامعتبر است')
        checked.append((vid,counted,expected,item.get('lot'),item.get('expiry_date'),item.get('serials')))
    cycle_id=str(uuid4());result=[];increased=0;decreased=0
    for vid,counted,expected,lot,expiry,serials in sorted(checked,key=lambda x:x[0]):
        if db.bind.dialect.name=='postgresql':
            db.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'),{'key':tid+':'+warehouse_id+':'+vid})
        row=db.query(Stock).filter_by(tenant_id=tid,warehouse_id=warehouse_id,variant_id=vid).with_for_update().first()
        current=row.quantity if row else 0
        reserved=row.reserved if row else 0
        if current!=expected:raise HTTPException(409,'موجودی کالا از زمان شمارش تغییر کرده است؛ دوباره بررسی کنید')
        if counted<reserved:raise HTTPException(409,'موجودی شمارش‌شده نمی‌تواند کمتر از رزرو باشد')
        delta=counted-current
        if delta:
            _stock(db,ctx,warehouse_id,vid,delta,'cycle_count',cycle_id,
                   note='ثبت انبارگردانی با مبنای موجودی '+str(expected),
                   lot=lot,expiry_date=expiry,serials=serials)
            cost=tenant_object(db,Variant,tid,vid).purchase_cost
            if delta>0:increased+=delta*cost
            else:decreased+=-delta*cost
        result.append({'variant_id':vid,'previous':current,'counted':counted,'difference':delta})
    postings=[]
    if increased:postings.extend([('1300',increased,0),('3000',0,increased)])
    if decreased:postings.extend([('6000',decreased,0),('1300',0,decreased)])
    if postings:_post_journal(db,ctx,'cycle-count:'+cycle_id,'ثبت مغایرت انبارگردانی',postings)
    db.add(EventKey(tenant_id=tid,kind='cycle_count',key=key,reference_id=cycle_id))
    audit(db,ctx,'cycle_count','stocks',cycle_id,{'warehouse_id':warehouse_id,'items':result})
    try:db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'انبارگردانی تکراری است')
    return {'id':cycle_id,'warehouse_id':warehouse_id,'items':result}

@app.post('/api/transfers')
def create_transfer(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,WAREHOUSE)
    qty=positive(body.get('quantity'))
    source=body.get('source_id');dest=body.get('destination_id');vid=body.get('variant_id')
    if source==dest:raise HTTPException(422,'انبار مبدأ و مقصد باید متفاوت باشند')
    for wid in (source,dest):tenant_object(db,Warehouse,ctx['tenant'],wid)
    tenant_object(db,Variant,ctx['tenant'],vid)
    obj=Transfer(tenant_id=ctx['tenant'],source_id=source,destination_id=dest,variant_id=vid,quantity=qty,actor_id=ctx['user'].id)
    db.add(obj);db.flush();audit(db,ctx,'create','transfers',obj.id);db.commit()
    return as_dict(obj)

@app.post('/api/transfers/{transfer_id}/{action}')
def transfer_action(transfer_id:str,action:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,WAREHOUSE)
    obj=tenant_object(db,Transfer,ctx['tenant'],transfer_id,lock=True)
    if action=='ship' and obj.status=='draft':
        _stock(db,ctx,obj.source_id,obj.variant_id,-obj.quantity,'transfer_ship',obj.id)
        obj.status='shipped'
    elif action=='receive' and obj.status=='shipped':
        _stock(db,ctx,obj.destination_id,obj.variant_id,obj.quantity,'transfer_receive',obj.id)
        obj.status='received'
    elif action=='cancel' and obj.status=='draft':
        obj.status='cancelled'
    else:raise HTTPException(409,'این تغییر وضعیت مجاز نیست')
    audit(db,ctx,action,'transfers',obj.id)
    db.commit();return as_dict(obj)

def _create_lines(db,tid,items,model,variant_ref,price_key):
    if not isinstance(items,list) or not items or len(items)>100:raise HTTPException(422,'حداقل یک قلم لازم است')
    result=[];total=0;seen=set()
    for data in items:
        if not isinstance(data,dict):raise HTTPException(422,'قلم نامعتبر')
        variant=tenant_object(db,Variant,tid,data.get('variant_id'))
        if variant.id in seen:raise HTTPException(422,'هر کالا را فقط یک‌بار در سند وارد کنید')
        seen.add(variant.id)
        if not variant.active:raise HTTPException(409,'تنوع غیرفعال است')
        qty=positive(data.get('quantity'))
        unit_price=amount(data.get(price_key,getattr(variant,variant_ref)),price_key)
        total+=unit_price*qty
        result.append((variant,qty,unit_price))
    if total>9_000_000_000_000_000:raise HTTPException(422,'مبلغ از سقف مجاز بیشتر است')
    return result,total

def _number(prefix):
    return prefix+'-'+datetime.now(timezone.utc).strftime('%y%m%d')+'-'+uuid4().hex[:9].upper()

@app.post('/api/purchases')
def create_purchase(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,PURCHASE)
    tid=ctx['tenant']
    supplier=tenant_object(db,Supplier,tid,body.get('supplier_id'))
    warehouse=tenant_object(db,Warehouse,tid,body.get('warehouse_id'))
    lines,total=_create_lines(db,tid,body.get('items'),PurchaseLine,'purchase_cost','cost')
    obj=PurchaseOrder(tenant_id=tid,supplier_id=supplier.id,warehouse_id=warehouse.id,number=_number('PO'),total=total)
    db.add(obj);db.flush()
    for variant,qty,cost in lines:
        db.add(PurchaseLine(tenant_id=tid,order_id=obj.id,variant_id=variant.id,quantity=qty,cost=cost))
    audit(db,ctx,'create','purchases',obj.id);db.commit()
    return as_dict(obj)

@app.post('/api/purchases/{purchase_id}/receive')
def receive_purchase(purchase_id:str,body:dict=Body(default={}),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,PURCHASE)
    order=tenant_object(db,PurchaseOrder,ctx['tenant'],purchase_id,lock=True)
    key=body.get('idempotency_key')
    if key:
        key=require_string(key,'شناسه درخواست',150)
        prior=db.query(EventKey).filter_by(tenant_id=ctx['tenant'],kind='purchase_receive',key=key).first()
        if prior:return {'duplicate':True,'order':as_dict(order)}
    if order.status in ('received','cancelled'):raise HTTPException(409,'سفارش قابل دریافت نیست')
    lines=db.query(PurchaseLine).filter_by(tenant_id=ctx['tenant'],order_id=order.id).with_for_update().all()
    provided=body.get('items')
    if provided is not None and (not isinstance(provided,list) or not provided):raise HTTPException(422,'اقلام نامعتبر')
    provided_map={}
    if provided:
        for item in provided:
            if not isinstance(item,dict) or not item.get('line_id') or item['line_id'] in provided_map:
                raise HTTPException(422,'ردیف دریافتی نامعتبر یا تکراری است')
            provided_map[item['line_id']]=item
    desired={line_id:positive(item.get('quantity')) for line_id,item in provided_map.items()} if provided else {l.id:l.quantity-l.received for l in lines if l.quantity>l.received}
    if not desired:raise HTTPException(409,'قلمی برای دریافت وجود ندارد')
    if set(desired)-{l.id for l in lines}:raise HTTPException(422,'ردیف غیرمجاز')
    received_value=0
    for line in lines:
        q=desired.get(line.id,0)
        if q:
            if q>line.quantity-line.received:raise HTTPException(409,'دریافت بیش از تعداد سفارش')
            meta=provided_map.get(line.id,{})
            _stock(db,ctx,order.warehouse_id,line.variant_id,q,'purchase_receive',order.id,lot=meta.get('lot'),expiry_date=meta.get('expiry_date'),serials=meta.get('serials'))
            line.received+=q
            received_value+=q*line.cost
    if received_value:
        _post_journal(db,ctx,'purchase-receive:'+order.id+':'+(key or uuid4().hex),
                      'دریافت سفارش خرید '+order.number,
                      [('1300',received_value,0),('2000',0,received_value)])
    order.status='received' if all(l.received==l.quantity for l in lines) else 'partial'
    audit(db,ctx,'receive','purchases',order.id,{'lines':desired})
    if key:db.add(EventKey(tenant_id=ctx['tenant'],kind='purchase_receive',key=key,reference_id=order.id))
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'دریافت تکراری است')
    return as_dict(order)

@app.post('/api/sales')
def create_sale(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,SALES)
    tid=ctx['tenant'];wh=tenant_object(db,Warehouse,tid,body.get('warehouse_id'))
    cid=body.get('customer_id')
    if cid:tenant_object(db,Customer,tid,cid)
    channel=body.get('channel','retail')
    if channel not in ('retail','wholesale','online','pos'):raise HTTPException(422,'کانال نامعتبر')
    lines,total=_create_lines(db,tid,body.get('items'),SalesLine,'wholesale_price' if channel=='wholesale' else 'retail_price','price')
    discount=amount(body.get('discount',0),'تخفیف')
    if discount>total:raise HTTPException(422,'تخفیف از کل بیشتر است')
    obj=SalesOrder(tenant_id=tid,customer_id=cid,warehouse_id=wh.id,number=_number('SO'),channel=channel,total=total-discount,discount=discount)
    db.add(obj);db.flush()
    for variant,qty,price in lines:
        db.add(SalesLine(tenant_id=tid,order_id=obj.id,variant_id=variant.id,quantity=qty,price=price,cost_snapshot=variant.purchase_cost))
    audit(db,ctx,'create','sales',obj.id);db.commit();return as_dict(obj)

def _fulfill_sale(db:Session,ctx,order:SalesOrder,desired:dict):
    if order.status not in ('confirmed','partial'):
        raise HTTPException(409,'سفارش برای ارسال آماده نیست')
    lines=db.query(SalesLine).filter_by(tenant_id=ctx['tenant'],
         order_id=order.id).order_by(SalesLine.id).with_for_update().all()
    valid={x.id:x for x in lines}
    if not desired or set(desired)-set(valid):
        raise HTTPException(422,'ردیف‌های ارسال نامعتبر هستند')
    for lid,qty in desired.items():
        positive(qty)
        line=valid[lid]
        if qty>line.quantity-line.fulfilled:
            raise HTTPException(409,'ارسال بیشتر از تعداد باقی‌مانده است')
    gross=sum(l.quantity*l.price for l in lines)
    already=sum(l.fulfilled*l.price for l in lines)
    dispatched=sum(valid[lid].price*qty for lid,qty in desired.items())
    revenue=(order.total*(already+dispatched)//gross-order.total*already//gross) if gross else 0
    cogs=sum(valid[lid].cost_snapshot*qty for lid,qty in desired.items())
    if revenue<0:raise HTTPException(409,'ارزش ارسالی نامعتبر است')
    snap=[]
    for lid,qty in sorted(desired.items()):
        ln=valid[lid]
        _stock(db,ctx,order.warehouse_id,ln.variant_id,-qty,'sale_fulfill',
               order.id,release_reserved=qty)
        ln.fulfilled+=qty
        snap.append({'line_id':lid,'variant_id':ln.variant_id,'quantity':qty,
                     'unit_price':ln.price,'cost_snapshot':ln.cost_snapshot})
    doc=Fulfillment(tenant_id=ctx['tenant'],order_id=order.id,
                    warehouse_id=order.warehouse_id,number=_number('FUL'),
                    status='shipped',items=snap,revenue=revenue,cost=cogs)
    db.add(doc);db.flush()
    postings=[]
    if revenue:postings.extend([('1200',int(revenue),0),('4000',0,int(revenue))])
    if cogs:postings.extend([('5000',int(cogs),0),('1300',0,int(cogs))])
    if postings:
        _post_journal(db,ctx,'fulfillment:'+doc.id,
                      'تحویل کالا از سفارش '+order.number,postings)
    order.status='fulfilled' if all(l.fulfilled==l.quantity for l in lines) else 'partial'
    audit(db,ctx,'fulfill','sales',order.id,{'fulfillment_id':doc.id,'items':snap})
    notification(db,ctx['tenant'],'بسته ارسالی ثبت شد',
                 f'محموله {doc.number} از سفارش {order.number} خارج شد.','shipping')
    return doc

@app.post('/api/sales/{sale_id}/fulfill-partial')
def fulfill_partial(sale_id:str,body:dict=Body(...),
                    db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,SALES|WAREHOUSE)
    key=require_string(body.get('idempotency_key'),'شناسه درخواست',150)
    tid=ctx['tenant']
    prior=db.query(EventKey).filter_by(tenant_id=tid,kind='partial_fulfill',key=key).first()
    if prior:
        doc=tenant_object(db,Fulfillment,tid,prior.reference_id)
        return {'duplicate':True,'fulfillment':as_dict(doc)}
    order=tenant_object(db,SalesOrder,tid,sale_id,lock=True)
    payload=body.get('items')
    if not isinstance(payload,list) or not 1<=len(payload)<=100:
        raise HTTPException(422,'حداقل یک قلم برای ارسال لازم است')
    desired={}
    for item in payload:
        if not isinstance(item,dict):
            raise HTTPException(422,'ردیف نامعتبر')
        lid=item.get('line_id')
        if not isinstance(lid,str) or lid in desired:
            raise HTTPException(422,'ردیف تکراری یا نامعتبر است')
        desired[lid]=positive(item.get('quantity'))
    doc=_fulfill_sale(db,ctx,order,desired)
    db.add(EventKey(tenant_id=tid,kind='partial_fulfill',key=key,reference_id=doc.id))
    try:db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'درخواست ارسال تکراری است')
    return {'duplicate':False,'fulfillment':as_dict(doc),'order':as_dict(order)}

@app.post('/api/sales/{sale_id}/{action}')
def sale_action(sale_id:str,action:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,SALES|WAREHOUSE if action=='fulfill' else SALES)
    order=tenant_object(db,SalesOrder,ctx['tenant'],sale_id,lock=True)
    lines=db.query(SalesLine).filter_by(tenant_id=ctx['tenant'],
                      order_id=order.id).order_by(SalesLine.id).with_for_update().all()
    counts={}
    for l in lines:counts[l.variant_id]=counts.get(l.variant_id,0)+l.quantity
    if action=='confirm' and order.status=='draft':
        for vid,qty in sorted(counts.items()):
            _stock(db,ctx,order.warehouse_id,vid,0,'reserve',order.id,reserve=qty)
        order.status='confirmed'
    elif action=='fulfill' and order.status in ('confirmed','partial'):
        desired={ln.id:ln.quantity-ln.fulfilled for ln in lines
                 if ln.quantity>ln.fulfilled}
        _fulfill_sale(db,ctx,order,desired)
    elif action=='cancel' and order.status in ('draft','confirmed'):
        if order.paid>0:
            raise HTTPException(409,'سفارش دارای پرداخت است؛ ابتدا استرداد را ثبت کنید')
        if order.status=='confirmed':
            for vid,qty in sorted(counts.items()):
                _stock(db,ctx,order.warehouse_id,vid,0,'unreserve',order.id,
                       release_reserved=qty)
        order.status='cancelled'
    else:
        raise HTTPException(409,'انتقال وضعیت غیرمجاز است')
    audit(db,ctx,action,'sales',order.id)
    db.commit()
    return as_dict(order)

@app.get('/api/fulfillments')
def list_fulfillments(page:int=Query(1,ge=1),limit:int=Query(30,ge=1,le=100),
                      db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,ALL)
    q=db.query(Fulfillment).filter_by(tenant_id=ctx['tenant'])
    total=q.count()
    rows=q.order_by(Fulfillment.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {'items':[as_dict(x) for x in rows],'total':total,'page':page,'limit':limit}

@app.patch('/api/fulfillments/{fulfillment_id}')
def update_fulfillment(fulfillment_id:str,body:dict=Body(...),
                       db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,SALES|WAREHOUSE)
    if not isinstance(body,dict) or set(body)-{'carrier','tracking_number','status'}:
        raise HTTPException(422,'فیلد نامعتبر')
    doc=tenant_object(db,Fulfillment,ctx['tenant'],fulfillment_id,lock=True)
    if doc.status=='delivered':
        raise HTTPException(409,'محموله تحویل‌شده قابل ویرایش نیست')
    if body.get('status',doc.status) not in ('shipped','delivered'):
        raise HTTPException(422,'وضعیت مجاز نیست')
    for key,value in body.items():
        if key in ('carrier','tracking_number'):
            if value is not None and (not isinstance(value,str) or len(value)>120):
                raise HTTPException(422,'مقدار نامعتبر')
        setattr(doc,key,value)
    audit(db,ctx,'update','fulfillments',doc.id,body)
    db.commit()
    return as_dict(doc)

@app.post('/api/invoices')
def issue_invoice(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    """Issue one immutable internal invoice for a confirmed/fulfilled sale."""
    authorized(ctx,SALES|FINANCE)
    tid=ctx['tenant']
    order=tenant_object(db,SalesOrder,tid,body.get('order_id'),lock=True)
    if order.status not in ('confirmed','fulfilled'):
        raise HTTPException(409,'فاکتور تنها برای فروش تأیید یا تحویل‌شده صادر می‌شود')
    existing=db.query(Invoice).filter_by(tenant_id=tid,order_id=order.id).first()
    if existing:return {'duplicate':True,'invoice':as_dict(existing)}
    lines=db.query(SalesLine).filter_by(tenant_id=tid,order_id=order.id).all()
    if not lines:raise HTTPException(409,'سفارش بدون قلم است')
    subtotal=sum(l.quantity*l.price for l in lines)
    if subtotal-order.discount!=order.total:
        raise HTTPException(409,'مبلغ سفارش و ردیف‌ها با هم سازگار نیستند')
    customer=tenant_object(db,Customer,tid,order.customer_id) if order.customer_id else None
    obj=Invoice(tenant_id=tid,order_id=order.id,number=_number('INV'),
                customer_name=customer.name if customer else 'مشتری حضوری',
                customer_address=customer.address or '' if customer else '',
                subtotal=subtotal,discount=order.discount,total=order.total,
                issuer_id=ctx['user'].id)
    db.add(obj);db.flush()
    for item in lines:
        var=tenant_object(db,Variant,tid,item.variant_id)
        db.add(InvoiceLine(tenant_id=tid,invoice_id=obj.id,variant_id=var.id,
                           sku_snapshot=var.sku,name_snapshot=var.name,
                           quantity=item.quantity,price=item.price))
    audit(db,ctx,'issue_invoice','invoices',obj.id,{'order_id':order.id})
    notification(db,tid,'فاکتور داخلی صادر شد',f'فاکتور {obj.number} برای سفارش {order.number} ثبت شد.','finance')
    try:db.commit()
    except IntegrityError:
        db.rollback()
        existing=db.query(Invoice).filter_by(tenant_id=tid,order_id=order.id).first()
        if existing:return {'duplicate':True,'invoice':as_dict(existing)}
        raise HTTPException(409,'شماره فاکتور تکراری یا نامعتبر است')
    return {'duplicate':False,'invoice':as_dict(obj)}

@app.get('/api/invoices')
def list_invoices(page:int=Query(1,ge=1,le=100000),limit:int=Query(25,ge=1,le=100),
                  db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,ALL)
    q=db.query(Invoice).filter_by(tenant_id=ctx['tenant'])
    total=q.count()
    records=q.order_by(Invoice.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {'items':[as_dict(x) for x in records],'total':total,'page':page,'limit':limit}

@app.get('/api/invoices/{invoice_id}')
def get_invoice(invoice_id:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,ALL)
    obj=tenant_object(db,Invoice,ctx['tenant'],invoice_id)
    rows=db.query(InvoiceLine).filter_by(tenant_id=ctx['tenant'],invoice_id=obj.id).all()
    company=db.get(Tenant,ctx['tenant'])
    return {'invoice':as_dict(obj),'items':[as_dict(x) for x in rows],
            'company':{'name':company.name,'phone':company.phone,'address':company.address}}

@app.get('/api/invoices/{invoice_id}/print',response_class=HTMLResponse)
def print_invoice(invoice_id:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    """Printable internal commercial invoice, not a certified tax invoice."""
    authorized(ctx,ALL)
    inv=tenant_object(db,Invoice,ctx['tenant'],invoice_id)
    company=db.get(Tenant,ctx['tenant'])
    rows=db.query(InvoiceLine).filter_by(tenant_id=ctx['tenant'],invoice_id=inv.id).all()
    safe=lambda v: html_escape(str(v or ''))
    formatted=lambda n: format(n,',')+' تومان'
    table_rows=''.join(
        '<tr><td>'+safe(x.sku_snapshot)+'</td><td>'+safe(x.name_snapshot)+'</td><td>'+str(x.quantity)+
        '</td><td>'+formatted(x.price)+'</td><td>'+formatted(x.quantity*x.price)+'</td></tr>'
        for x in rows)
    html_doc='''<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>فاکتور داخلی</title><style>
    body{font-family:Tahoma,Arial,sans-serif;margin:36px;color:#1b263a;line-height:1.8}
    header{display:flex;justify-content:space-between;gap:20px;border-bottom:2px solid #d4deeb;padding-bottom:18px}
    h1{font-size:24px;margin:0}small{color:#666}table{border-collapse:collapse;width:100%;margin-top:30px}
    th,td{border:1px solid #d3dae6;padding:12px;text-align:right}th{background:#f4f6fa}
    .total{margin-top:22px;text-align:left;font-weight:bold}.no-tax{margin-top:30px;font-size:12px;color:#666}
    button{border:0;border-radius:8px;background:#245eab;color:white;padding:10px 20px;cursor:pointer}
    @media print{button{display:none}body{margin:20px}}
    </style></head><body><button onclick="window.print()">چاپ فاکتور</button>
    <header><div><h1>فاکتور فروش داخلی</h1><strong>'''+safe(company.name)+'''</strong>
    <p>'''+safe(company.address)+'''</p></div><div><div>شماره: '''+safe(inv.number)+'''
    </div><small>تاریخ: '''+safe(inv.created_at.strftime('%Y-%m-%d'))+'''</small></div></header>
    <p>خریدار: <strong>'''+safe(inv.customer_name)+'''</strong></p>
    <p>نشانی: '''+safe(inv.customer_address)+'''</p>
    <table><thead><tr><th>SKU</th><th>کالا</th><th>تعداد</th><th>قیمت واحد</th><th>مبلغ</th></tr></thead>
    <tbody>'''+table_rows+'''</tbody></table>
    <div class="total">جمع ردیف‌ها: '''+formatted(inv.subtotal)+'''<br>
    تخفیف: '''+formatted(inv.discount)+'''<br>مبلغ نهایی: '''+formatted(inv.total)+'''</div>
    <div class="no-tax">این سند فاکتور داخلی فروشگاه است و فاکتور رسمی یا دارای تأییدیه سازمان امور مالیاتی نیست.</div>
    </body></html>'''
    return HTMLResponse(html_doc)

@app.post('/api/payments')
def record_payment(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,SALES|FINANCE)
    tid=ctx['tenant'];key=require_string(body.get('idempotency_key'),'شناسه یکتا',120)
    v=positive_amount(body.get('amount'),'مبلغ')
    sale_id=body.get('sale_id');purchase_id=body.get('purchase_id')
    existing=db.query(Payment).filter_by(tenant_id=tid,idempotency_key=key).first()
    if existing:
        if (existing.amount != v or existing.order_id != sale_id or
                existing.purchase_id != purchase_id or existing.method != body.get('method','cash')):
            raise HTTPException(409,'شناسه یکتا قبلاً برای پرداخت متفاوتی استفاده شده است')
        return {'duplicate':True,'payment':as_dict(existing)}
    if bool(sale_id)==bool(purchase_id):raise HTTPException(422,'فقط یک سند فروش یا خرید تعیین کنید')
    if purchase_id:authorized(ctx,FINANCE)
    doc=tenant_object(db,SalesOrder if sale_id else PurchaseOrder,tid,sale_id or purchase_id,lock=True)
    if doc.status=='cancelled':raise HTTPException(409,'سند لغوشده قابل پرداخت نیست')
    if v>doc.total-doc.paid:raise HTTPException(409,'پرداخت از مانده بیشتر است')
    method=body.get('method','cash')
    if method not in ('cash','card','transfer','online'):raise HTTPException(422,'روش پرداخت نامعتبر')
    obj=Payment(tenant_id=tid,order_id=sale_id,purchase_id=purchase_id,amount=v,method=method,idempotency_key=key,actor_id=ctx['user'].id)
    db.add(obj);db.flush()
    doc.paid+=v
    account_id=body.get('account_id')
    if account_id:
        tenant_object(db,CashAccount,tid,account_id)
        db.add(AccountEntry(tenant_id=tid,account_id=account_id,direction='in' if sale_id else 'out',amount=v,reference=obj.id,note='دریافت سفارش' if sale_id else 'پرداخت خرید'))
    cash_code='1020' if (account_id and db.get(CashAccount,account_id).type=='bank') else '1010'
    if sale_id:
        _post_journal(db,ctx,'payment:'+obj.id,'دریافت بابت فروش '+doc.number,
                      [(cash_code,v,0),('1200',0,v)])
    else:
        _post_journal(db,ctx,'payment:'+obj.id,'پرداخت بابت خرید '+doc.number,
                      [('2000',v,0),(cash_code,0,v)])
    if sale_id:
        notification(db,tid,'پرداخت موفق',f'پرداخت {v:,} تومان برای سفارش {doc.number} ثبت شد.','payment')
    audit(db,ctx,'record','payments',obj.id,{'amount':v})
    try:db.commit()
    except IntegrityError:
        db.rollback()
        existing=db.query(Payment).filter_by(tenant_id=tid,idempotency_key=key).first()
        if existing:return {'duplicate':True,'payment':as_dict(existing)}
        raise HTTPException(409,'پرداخت تکراری یا نامعتبر')
    return {'duplicate':False,'payment':as_dict(obj)}

@app.post('/api/returns')
def record_return(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    tid=ctx['tenant'];direction=body.get('direction')
    authorized(ctx,SALES if direction=='sale' else PURCHASE)
    if direction not in ('sale','purchase'):raise HTTPException(422,'نوع مرجوعی نامعتبر')
    key=body.get('idempotency_key')
    if key:
        key=require_string(key,'شناسه درخواست',150)
        previous=db.query(EventKey).filter_by(tenant_id=tid,kind='return',key=key).first()
        if previous:return {'duplicate':True,'return_id':previous.reference_id}
    id_=body.get('order_id')
    doc=tenant_object(db,SalesOrder if direction=='sale' else PurchaseOrder,tid,id_,lock=True)
    if direction=='sale' and doc.status not in ('fulfilled','partial'):raise HTTPException(409,'فقط فروش تحویل‌شده مرجوع می‌شود')
    if direction=='purchase' and doc.status not in ('received','partial'):raise HTTPException(409,'این خرید هنوز دریافت نشده است')
    vid=body.get('variant_id');qty=positive(body.get('quantity'))
    line_model=SalesLine if direction=='sale' else PurchaseLine
    line=db.query(line_model).filter_by(tenant_id=tid,order_id=doc.id,variant_id=vid).with_for_update().first()
    if not line:raise HTTPException(422,'کالا در سند وجود ندارد')
    if direction=='sale':
        if qty>line.fulfilled-line.returned:raise HTTPException(409,'تعداد مرجوعی از کالای تحویل‌شده بیشتر است')
        line.returned+=qty
    else:
        prior=db.query(func.coalesce(func.sum(Return.quantity),0)).filter_by(tenant_id=tid,purchase_id=doc.id,variant_id=vid,direction='purchase').scalar()
        if qty>line.received-int(prior):raise HTTPException(409,'مرجوعی از دریافتی بیشتر است')
    restock=bool(body.get('restock',True))
    if direction=='purchase':_stock(db,ctx,doc.warehouse_id,vid,-qty,'supplier_return',doc.id)
    elif restock:_stock(db,ctx,doc.warehouse_id,vid,qty,'customer_return',doc.id,serials=body.get('serials'))
    obj=Return(tenant_id=tid,direction=direction,order_id=doc.id if direction=='sale' else None,purchase_id=doc.id if direction=='purchase' else None,variant_id=vid,warehouse_id=doc.warehouse_id,quantity=qty,amount=qty*(line.price if direction=='sale' else line.cost),restock=restock)
    db.add(obj);db.flush()
    postings=[]
    if obj.amount:
        if direction=='sale':
            postings.extend([('4100',obj.amount,0),('1200',0,obj.amount)])
        else:
            postings.extend([('2000',obj.amount,0),('1300',0,obj.amount)])
    if direction=='sale' and restock and line.cost_snapshot>0:
        value=qty*line.cost_snapshot
        postings.extend([('1300',value,0),('5000',0,value)])
    if postings:
        _post_journal(db,ctx,'return:'+obj.id,'مرجوعی '+direction,postings)
    audit(db,ctx,'create','returns',obj.id)
    if key:db.add(EventKey(tenant_id=tid,kind='return',key=key,reference_id=obj.id))
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'درخواست مرجوعی تکراری است')
    return as_dict(obj)

def _settlement_state(db:Session,ctx,return_id:str):
    obj=tenant_object(db,Return,ctx['tenant'],return_id,lock=True)
    doc=tenant_object(db,SalesOrder if obj.direction=='sale' else PurchaseOrder,
                      ctx['tenant'],obj.order_id or obj.purchase_id,lock=True)
    used=int(db.query(func.coalesce(func.sum(AccountEntry.amount),0)).filter(
        AccountEntry.tenant_id==ctx['tenant'],AccountEntry.reference==obj.id,
        AccountEntry.direction==('out' if obj.direction=='sale' else 'in')).scalar() or 0)
    linked=db.query(Return.id).filter_by(tenant_id=ctx['tenant'],direction=obj.direction,
                    **({'order_id':doc.id} if obj.direction=='sale' else {'purchase_id':doc.id})).all()
    ids=[row[0] for row in linked]
    all_used=int(db.query(func.coalesce(func.sum(AccountEntry.amount),0)).filter(
        AccountEntry.tenant_id==ctx['tenant'],AccountEntry.reference.in_(ids),
        AccountEntry.direction==('out' if obj.direction=='sale' else 'in')).scalar() or 0)
    remaining=max(0,min(obj.amount-used,doc.paid-all_used))
    return obj,doc,used,remaining

@app.get('/api/returns/{return_id}/settlement')
def return_settlement_state(return_id:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE)
    obj,doc,used,remaining=_settlement_state(db,ctx,return_id)
    return {'return_id':obj.id,'direction':obj.direction,'return_amount':obj.amount,
            'settled':used,'remaining':remaining,'document_number':doc.number}

@app.post('/api/returns/{return_id}/settle')
def settle_return(return_id:str,body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    """Manually record a return refund or supplier reimbursement, never a gateway charge."""
    authorized(ctx,FINANCE)
    tid=ctx['tenant']
    obj,doc,used,remaining=_settlement_state(db,ctx,return_id)
    key=require_string(body.get('idempotency_key'),'شناسه یکتا',150)
    if db.query(EventKey).filter_by(tenant_id=tid,kind='return_settlement',key=key).first():
        raise HTTPException(409,'این تسویه قبلاً ثبت شده است')
    value=positive_amount(body.get('amount'),'مبلغ')
    if value>remaining:raise HTTPException(409,'مبلغ بیشتر از مانده قابل تسویه است')
    account=tenant_object(db,CashAccount,tid,body.get('account_id'))
    direction='out' if obj.direction=='sale' else 'in'
    entry=AccountEntry(tenant_id=tid,account_id=account.id,direction=direction,amount=value,
                       reference=obj.id,note='تسویه مرجوعی '+doc.number)
    db.add(entry);db.flush()
    cash_code='1020' if account.type=='bank' else '1010'
    postings=([('1200',value,0),(cash_code,0,value)] if obj.direction=='sale'
              else [(cash_code,value,0),('2000',0,value)])
    _post_journal(db,ctx,'return-settle:'+key,'تسویه مرجوعی '+doc.number,postings)
    db.add(EventKey(tenant_id=tid,kind='return_settlement',key=key,reference_id=obj.id))
    audit(db,ctx,'settle_return','returns',obj.id,{'amount':value,'account_id':account.id})
    notification(db,tid,'تسویه مرجوعی',f'تسویه {value:,} تومان برای {doc.number} ثبت شد.','finance')
    try:db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'تسویه تکراری یا نامعتبر است')
    return {'entry':as_dict(entry),'remaining':remaining-value}

@app.get('/api/dashboard')
def dashboard(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    tid=ctx['tenant']
    def scalar(q):return int(q.scalar() or 0)
    sales=scalar(db.query(func.coalesce(func.sum(SalesOrder.total),0)).filter(SalesOrder.tenant_id==tid,SalesOrder.status!='cancelled'))
    sales_paid=scalar(db.query(func.coalesce(func.sum(SalesOrder.paid),0)).filter(SalesOrder.tenant_id==tid))
    purchase=scalar(db.query(func.coalesce(func.sum(PurchaseOrder.total),0)).filter(PurchaseOrder.tenant_id==tid,PurchaseOrder.status!='cancelled'))
    stock_count=scalar(db.query(func.coalesce(func.sum(Stock.quantity),0)).filter_by(tenant_id=tid))
    stock_value=scalar(db.query(func.coalesce(func.sum(Stock.quantity*Variant.purchase_cost),0)).join(Variant,Stock.variant_id==Variant.id).filter(Stock.tenant_id==tid,Variant.tenant_id==tid))
    due_sales=scalar(db.query(func.coalesce(func.sum(SalesOrder.total-SalesOrder.paid),0)).filter(SalesOrder.tenant_id==tid,SalesOrder.status!='cancelled'))
    low=db.query(Variant).filter_by(tenant_id=tid,active=True).all()
    low_count=sum(1 for v in low if scalar(db.query(func.coalesce(func.sum(Stock.quantity-Stock.reserved),0)).filter_by(tenant_id=tid,variant_id=v.id))<=v.low_stock)
    notifications=db.query(Notification).filter_by(tenant_id=tid,read=False).order_by(Notification.created_at.desc()).limit(10).all()
    return {'sales':sales,'sales_paid':sales_paid,'purchase':purchase,'stock_count':stock_count,'stock_value':stock_value,
            'receivables':due_sales,'low_stock':low_count,'orders':db.query(SalesOrder).filter_by(tenant_id=tid).count(),
            'unread':len(notifications),'notifications':[as_dict(x) for x in notifications]}

@app.get('/api/reports')
def reports(type:str='sales',db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    tid=ctx['tenant']
    if type=='sales':
        rows=db.query(SalesOrder).filter_by(tenant_id=tid).order_by(SalesOrder.created_at.desc()).limit(1000).all()
        return {'rows':[{'number':x.number,'status':x.status,'channel':x.channel,'total':x.total,'paid':x.paid,'date':x.created_at.isoformat()} for x in rows]}
    if type=='inventory':
        rows=db.query(Stock,Variant,Warehouse).join(Variant,Stock.variant_id==Variant.id).join(Warehouse,Stock.warehouse_id==Warehouse.id).filter(Stock.tenant_id==tid,Variant.tenant_id==tid,Warehouse.tenant_id==tid).limit(2000).all()
        return {'rows':[{'sku':v.sku,'warehouse':w.name,'quantity':s.quantity,'reserved':s.reserved,'value':s.quantity*v.purchase_cost} for s,v,w in rows]}
    if type=='receivables':
        rows=db.query(SalesOrder).filter(SalesOrder.tenant_id==tid,SalesOrder.total>SalesOrder.paid,SalesOrder.status!='cancelled').all()
        return {'rows':[{'number':x.number,'due':x.total-x.paid,'customer_id':x.customer_id} for x in rows]}
    if type=='payables':
        rows=db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id==tid,PurchaseOrder.total>PurchaseOrder.paid,PurchaseOrder.status!='cancelled').all()
        return {'rows':[{'number':x.number,'due':x.total-x.paid,'supplier_id':x.supplier_id} for x in rows]}
    if type=='margins':
        rows=db.query(SalesLine,SalesOrder).join(SalesOrder,SalesLine.order_id==SalesOrder.id).filter(SalesLine.tenant_id==tid,SalesOrder.tenant_id==tid,SalesOrder.status=='fulfilled').all()
        return {'rows':[{'sku':db.get(Variant,l.variant_id).sku,'quantity':l.quantity,'revenue':l.quantity*l.price,'cost':l.quantity*l.cost_snapshot,'gross_margin':l.quantity*(l.price-l.cost_snapshot)} for l,_ in rows]}
    raise HTTPException(422,'نوع گزارش نامعتبر')

@app.post('/api/notifications/{notification_id}/read')
def read_notification(notification_id:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    obj=tenant_object(db,Notification,ctx['tenant'],notification_id)
    obj.read=True;db.commit();return {'ok':True}

@app.get('/api/public-mode')
def public_mode():
    """Safe, non-sensitive UI hint to avoid displaying a sign-in form in showroom mode."""
    return {'enabled':public_demo_enabled(),'mode':'read-only' if public_demo_enabled() else 'private'}

@app.get('/api/health')
def health():return {'ok':True,'service':'store-erp'}

@app.get('/api/ready')
def ready(db:Session=Depends(db_session)):
    try:
        db.execute(text('SELECT 1'))
    except Exception:
        raise HTTPException(503,'دیتابیس در دسترس نیست')
    return {'ok':True,'database':'connected'}

@app.get('/api/settings')
def settings(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    return as_dict(db.get(Tenant,ctx['tenant']))

@app.patch('/api/settings')
def update_settings(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,{'owner','admin'})
    if set(body)-{'name','phone','address'}:raise HTTPException(422,'فیلد نامعتبر')
    tenant=db.get(Tenant,ctx['tenant'])
    if 'name' in body: tenant.name=require_string(body['name'],'نام کسب‌وکار',200)
    for field in ('phone','address'):
        if field in body:setattr(tenant,field,body[field])
    audit(db,ctx,'update','tenant',ctx['tenant'])
    db.commit();return as_dict(tenant)

@app.get('/api/members')
def members(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,{'owner','admin'})
    rows=db.query(Member,User).join(User,Member.user_id==User.id).filter(Member.tenant_id==ctx['tenant']).all()
    return {'items':[{'id':m.id,'name':u.name,'email':u.email,'role':m.role,'active':m.active} for m,u in rows]}

@app.patch('/api/members/{member_id}')
def change_member(member_id:str,body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,{'owner','admin'})
    membership=tenant_object(db,Member,ctx['tenant'],member_id,lock=True)
    new_role=body.get('role',membership.role)
    new_active=body.get('active',membership.active)
    if new_role not in ROLES or type(new_active) is not bool:raise HTTPException(422,'نقش یا وضعیت نامعتبر')
    if ctx['role']!='owner' and ('owner' in (new_role,membership.role)):
        raise HTTPException(403,'تغییر مالک فقط توسط مالک دیگر')
    if membership.user_id==ctx['user'].id and (not new_active or new_role!=membership.role):
        raise HTTPException(409,'نقش یا عضویت فعلی خودتان را تغییر ندهید')
    if membership.role=='owner' and (new_role!='owner' or not new_active):
        count=db.query(Member).filter_by(tenant_id=ctx['tenant'],role='owner',active=True).count()
        if count<=1:raise HTTPException(409,'آخرین مالک قابل حذف نیست')
    membership.role=new_role;membership.active=new_active
    audit(db,ctx,'update','member',membership.id)
    db.commit();return {'ok':True}

import hashlib as _hashlib
import secrets as _secrets
@app.post('/api/invites')
def invite(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,{'owner','admin'})
    email=require_string(body.get('email'),'ایمیل',254).lower()
    role=body.get('role','viewer')
    if role not in ROLES or role=='owner':raise HTTPException(422,'نقش نامعتبر')
    key=_secrets.token_urlsafe(32)
    invite=Invite(tenant_id=ctx['tenant'],email=email,role=role,token_hash=_hashlib.sha256(key.encode()).hexdigest(),expires_at=datetime.now(timezone.utc)+timedelta(days=7))
    db.add(invite);db.flush();audit(db,ctx,'invite','member',invite.id);db.commit()
    return {'token':key,'expires_at':invite.expires_at.isoformat(),'email':email,'role':role}

def _lookup_invite(db,key,email):
    if not isinstance(key,str) or len(key)>200:raise HTTPException(422,'کد دعوت نامعتبر')
    digest=_hashlib.sha256(key.encode()).hexdigest()
    inv=db.query(Invite).filter_by(token_hash=digest).with_for_update().first()
    if not inv or inv.used_at or inv.email!=email or inv.expires_at.replace(tzinfo=timezone.utc)<datetime.now(timezone.utc):
        raise HTTPException(403,'دعوت منقضی یا نامعتبر است')
    return inv

@app.post('/api/auth/accept-invite')
def accept_invite(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    inv=_lookup_invite(db,body.get('token'),ctx['user'].email)
    if db.query(Member).filter_by(tenant_id=inv.tenant_id,user_id=ctx['user'].id).first():
        raise HTTPException(409,'قبلاً عضو این سازمان هستید')
    member=Member(tenant_id=inv.tenant_id,user_id=ctx['user'].id,role=inv.role)
    db.add(member);inv.used_at=datetime.now(timezone.utc);db.commit()
    response=JSONResponse({'ok':True,'tenant_id':inv.tenant_id})
    secure_cookie(response,_persist_session(db,issue_token(ctx['user'].id,inv.tenant_id)))
    return response

@app.get('/api/organizations')
def organizations(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    members=db.query(Member,Tenant).join(Tenant,Member.tenant_id==Tenant.id).filter(Member.user_id==ctx['user'].id,Member.active==True).all()
    return {'items':[{'id':t.id,'name':t.name,'role':m.role} for m,t in members]}

@app.post('/api/organizations/switch')
def switch_org(body:dict=Body(...),db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    membership=db.query(Member).filter_by(user_id=ctx['user'].id,tenant_id=body.get('tenant_id'),active=True).first()
    if not membership:raise HTTPException(403,'عضویت ندارید')
    response=JSONResponse({'ok':True})
    secure_cookie(response,_persist_session(db,issue_token(ctx['user'].id,membership.tenant_id)))
    return response

@app.get('/api/documents/{kind}/{document_id}/lines')
def document_lines(kind:str,document_id:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    if kind not in ('sales','purchases'):raise HTTPException(404,'نوع سند نامعتبر')
    model=SalesOrder if kind=='sales' else PurchaseOrder
    line_model=SalesLine if kind=='sales' else PurchaseLine
    tenant_object(db,model,ctx['tenant'],document_id)
    lines=db.query(line_model).filter_by(tenant_id=ctx['tenant'],order_id=document_id).all()
    return {'items':[as_dict(l) for l in lines]}

@app.get('/api/ledger/accounts')
def ledger_accounts(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE|{'viewer'})
    accounts=db.query(LedgerAccount).filter_by(tenant_id=ctx['tenant']).order_by(LedgerAccount.code).all()
    return {'items':[as_dict(x) for x in accounts],'total':len(accounts)}

@app.post('/api/ledger/bootstrap')
def ledger_bootstrap(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE)
    data=_ensure_ledger(db,ctx['tenant'])
    db.commit()
    return {'ok':True,'total':len(data)}

@app.post('/api/ledger/accounts')
def ledger_account_create(body:dict=Body(...),db:Session=Depends(db_session),
                          ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE)
    code=require_string(body.get('code'),'کد حساب',20)
    name=require_string(body.get('name'),'نام حساب',180)
    kind=body.get('kind')
    if kind not in ('asset','liability','equity','revenue','expense'):
        raise HTTPException(422,'نوع حساب نامعتبر است')
    if not code.isdigit():raise HTTPException(422,'کد حساب فقط باید عدد باشد')
    obj=LedgerAccount(tenant_id=ctx['tenant'],code=code,name=name,kind=kind,active=True)
    db.add(obj);audit(db,ctx,'create','ledger_accounts',obj.id)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'کد حساب تکراری است')
    return as_dict(obj)

@app.get('/api/ledger/journals')
def ledger_journals(page:int=Query(1,ge=1,le=100000),limit:int=Query(40,ge=1,le=100),
                    start:date|None=None,end:date|None=None,
                    db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE|{'viewer'})
    q=db.query(Journal).filter_by(tenant_id=ctx['tenant'])
    if start:q=q.filter(Journal.journal_date>=start)
    if end:q=q.filter(Journal.journal_date<=end)
    total=q.count()
    entries=q.order_by(Journal.journal_date.desc(),Journal.created_at.desc()).offset(
        (page-1)*limit).limit(limit).all()
    return {'items':[as_dict(x) for x in entries],'page':page,'limit':limit,'total':total}

@app.get('/api/ledger/journals/{entry_id}')
def ledger_journal(entry_id:str,db:Session=Depends(db_session),
                   ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE|{'viewer'})
    doc=tenant_object(db,Journal,ctx['tenant'],entry_id)
    lines=db.query(JournalLine).filter_by(tenant_id=ctx['tenant'],journal_id=doc.id).all()
    return {'journal':as_dict(doc),'lines':[as_dict(x) for x in lines]}

@app.post('/api/ledger/journals')
def ledger_journal_create(body:dict=Body(...),db:Session=Depends(db_session),
                          ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE)
    key=require_string(body.get('idempotency_key'),'شناسه یکتا',150)
    source='manual:'+key
    if db.query(Journal).filter_by(tenant_id=ctx['tenant'],source_key=source).first():
        raise HTTPException(409,'این سند قبلاً ثبت شده است')
    raw=body.get('lines')
    if not isinstance(raw,list) or len(raw)<2 or len(raw)>50:
        raise HTTPException(422,'سند باید بین ۲ تا ۵۰ ردیف داشته باشد')
    lines=[]
    for item in raw:
        if not isinstance(item,dict):raise HTTPException(422,'ردیف نامعتبر')
        account=tenant_object(db,LedgerAccount,ctx['tenant'],item.get('account_id'))
        if not account.active:raise HTTPException(409,'حساب غیرفعال')
        debit=amount(item.get('debit',0),'بدهکار')
        credit=amount(item.get('credit',0),'بستانکار')
        lines.append((account.code,debit,credit))
    memo=require_string(body.get('memo'),'شرح سند',900)
    doc=_post_journal(db,ctx,source,memo,lines)
    audit(db,ctx,'create','journals',doc.id)
    try:db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'شماره یا شناسه سند تکراری است')
    return {'journal':as_dict(doc),'total':sum(line[1] for line in lines)}

@app.get('/api/ledger/trial-balance')
def trial_balance(start:date|None=None,end:date|None=None,
                  db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE|{'viewer'})
    tid=ctx['tenant']
    accounts=db.query(LedgerAccount).filter_by(tenant_id=tid).order_by(LedgerAccount.code).all()
    qry=db.query(JournalLine,Journal).join(Journal,JournalLine.journal_id==Journal.id).filter(
        JournalLine.tenant_id==tid,Journal.tenant_id==tid)
    if start:qry=qry.filter(Journal.journal_date>=start)
    if end:qry=qry.filter(Journal.journal_date<=end)
    sums={}
    for line,_ in qry.all():
        current=sums.setdefault(line.account_id,[0,0])
        current[0]+=line.debit;current[1]+=line.credit
    items=[{**as_dict(a),'debit':sums.get(a.id,[0,0])[0],
             'credit':sums.get(a.id,[0,0])[1],
             'balance':sums.get(a.id,[0,0])[0]-sums.get(a.id,[0,0])[1]}
             for a in accounts]
    debits=sum(x['debit'] for x in items);credits=sum(x['credit'] for x in items)
    return {'items':items,'total_debit':debits,'total_credit':credits,
            'balanced':debits==credits,'start':start.isoformat() if start else None,
            'end':end.isoformat() if end else None}

@app.get('/api/ledger/profit-loss')
def profit_loss(start:date|None=None,end:date|None=None,
                db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,FINANCE|{'viewer'})
    balance=trial_balance(start,end,db,ctx)
    rev=sum(a['credit']-a['debit'] for a in balance['items'] if a['kind']=='revenue')
    expenses=sum(a['debit']-a['credit'] for a in balance['items'] if a['kind']=='expense')
    return {'revenue':rev,'expenses':expenses,'net_profit':rev-expenses,
            'balanced':balance['balanced'],'currency':'TOMAN',
            'account_totals':[x for x in balance['items']
                if x['kind'] in ('revenue','expense')]}


# Provider-neutral external integrations. The server never stores API tokens in
# tenant settings; purchasing a provider is not necessary to inspect its setup.
INTEGRATION_TYPES={
 'payment':{'label':'درگاه پرداخت','providers':['zarinpal','mellat','idpay','other'],
            'fields':['callback_url'],'env':'PAYMENT_GATEWAY_SECRET'},
 'sms':{'label':'پنل پیامک','providers':['kavenegar','farazsms','melipayamak','other'],
        'fields':['sender'],'env':'SMS_PROVIDER_API_KEY'},
 'email':{'label':'ارسال ایمیل','providers':['smtp','resend','other'],
          'fields':['sender_email'],'env':'EMAIL_PROVIDER_API_KEY'},
 'storage':{'label':'فضای ذخیره‌سازی S3','providers':['parspack','minio','aws','other'],
            'fields':['bucket','endpoint'],'env':'S3_ACCESS_KEY'},
 'shipping':{'label':'سامانه ارسال مرسوله','providers':['post','tipax','chapar','other'],
             'fields':['origin_city'],'env':'SHIPPING_PROVIDER_TOKEN'},
 'storefront':{'label':'اتصال فروشگاه آنلاین','providers':['nextjs','woocommerce','custom'],
               'fields':['store_name','base_url'],'env':'STOREFRONT_API_TOKEN'},
}
@app.get('/api/integrations')
def integration_list(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,ALL)
    rows={r.kind:r for r in db.query(Integration).filter_by(tenant_id=ctx['tenant']).all()}
    result=[]
    for kind,meta in INTEGRATION_TYPES.items():
        item=rows.get(kind)
        result.append({'kind':kind,'label':meta['label'],'providers':meta['providers'],
                       'fields':meta['fields'],'provider':item.provider if item else '',
                       'settings':item.settings if item else {},'enabled':False,
                       'status':'نیازمند اتصال سرویس خارجی',
                       'required_env':meta['env']})
    return {'items':result}

@app.put('/api/integrations/{kind}')
def integration_update(kind:str,body:dict=Body(...),db:Session=Depends(db_session),
                       ctx:dict=Depends(principal)):
    authorized(ctx,{'owner','admin'})
    meta=INTEGRATION_TYPES.get(kind)
    if not meta:raise HTTPException(404,'سرویس تعریف نشده است')
    provider=body.get('provider')
    if provider not in meta['providers']:raise HTTPException(422,'ارائه‌دهنده نامعتبر')
    settings=body.get('settings',{})
    if not isinstance(settings,dict) or set(settings)-set(meta['fields']):
        raise HTTPException(422,'فیلدهای غیرمجاز یا محرمانه ارسال شده است')
    clean={}
    for k,v in settings.items():
        if not isinstance(v,str) or len(v)>300:raise HTTPException(422,'مقدار تنظیمات نامعتبر است')
        if k in ('base_url','callback_url','endpoint') and v and not v.startswith('https://'):
            raise HTTPException(422,'نشانی سرویس باید HTTPS باشد')
        clean[k]=v.strip()
    item=db.query(Integration).filter_by(tenant_id=ctx['tenant'],kind=kind).with_for_update().first()
    if not item:
        item=Integration(tenant_id=ctx['tenant'],kind=kind)
        db.add(item)
    item.provider=provider;item.settings=clean;item.enabled=False
    db.flush();audit(db,ctx,'configure','integrations',item.id,{'kind':kind,'provider':provider})
    db.commit()
    return {'ok':True,'enabled':False,'message':'تنظیمات غیرمحرمانه ذخیره شد؛ اتصال واقعی هنوز غیرفعال است'}

@app.post('/api/integrations/{kind}/activate')
def integration_activate(kind:str,ctx:dict=Depends(principal)):
    authorized(ctx,{'owner','admin'})
    if kind not in INTEGRATION_TYPES:raise HTTPException(404,'سرویس تعریف نشده است')
    raise HTTPException(501,'اتصال واقعی تا دریافت اطلاعات سرویس و پیاده‌سازی و تست آداپتور غیرفعال است')

@app.get('/api/stock/expiry-alerts')
def expiry_alerts(days:int=Query(60,ge=0,le=730),
                  page:int=Query(1,ge=1),limit:int=Query(50,ge=1,le=100),
                  db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,ALL)
    limit_date=date.today()+timedelta(days=days)
    q=db.query(StockBatch,Variant,Warehouse).join(
        Variant,StockBatch.variant_id==Variant.id).join(
        Warehouse,StockBatch.warehouse_id==Warehouse.id).filter(
        StockBatch.tenant_id==ctx['tenant'],Variant.tenant_id==ctx['tenant'],
        Warehouse.tenant_id==ctx['tenant'],StockBatch.quantity>0,
        StockBatch.expiry_date!=None,StockBatch.expiry_date<=limit_date)
    total=q.count()
    results=q.order_by(StockBatch.expiry_date.asc()).offset((page-1)*limit).limit(limit).all()
    return {'total':total,'page':page,'items':[
        {'lot_id':b.id,'lot':b.lot,'warehouse':w.name,'sku':v.sku,'variant_id':v.id,
         'quantity':b.quantity,'expiry_date':b.expiry_date.isoformat(),
         'days_left':(b.expiry_date-date.today()).days}
        for b,v,w in results]}

@app.get('/api/analytics')
def business_analytics(start:date|None=None,end:date|None=None,
                       db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,ALL)
    period_end=end or date.today()
    period_start=start or (period_end-timedelta(days=89))
    if period_start>period_end or (period_end-period_start).days>366:
        raise HTTPException(422,'بازه گزارش نباید بیشتر از یک سال باشد')
    tid=ctx['tenant']
    sales=db.query(SalesOrder).filter(SalesOrder.tenant_id==tid,
        SalesOrder.created_at>=datetime.combine(period_start,datetime.min.time(),tzinfo=timezone.utc),
        SalesOrder.created_at<datetime.combine(period_end+timedelta(days=1),datetime.min.time(),tzinfo=timezone.utc),
        SalesOrder.status.in_(['confirmed','fulfilled'])).all()
    channels={};daily={}
    for o in sales:
        key=o.created_at.date().isoformat()
        v=daily.setdefault(key,{'date':key,'orders':0,'sales':0})
        v['orders']+=1;v['sales']+=o.total
        c=channels.setdefault(o.channel,{'channel':o.channel,'orders':0,'sales':0})
        c['orders']+=1;c['sales']+=o.total
    order_ids=[o.id for o in sales]
    top=[]
    if order_ids:
        rows=db.query(SalesLine.variant_id,
                      func.sum(SalesLine.quantity).label('qty'),
                      func.sum(SalesLine.quantity*SalesLine.price).label('sales'),
                      func.sum(SalesLine.quantity*(SalesLine.price-SalesLine.cost_snapshot)).label('margin')
                      ).filter(SalesLine.tenant_id==tid,
                              SalesLine.order_id.in_(order_ids)).group_by(
                                  SalesLine.variant_id).order_by(
                                      func.sum(SalesLine.quantity*SalesLine.price).desc()).limit(10).all()
        for vid,qty,revenue,margin in rows:
            v=db.get(Variant,vid)
            top.append({'sku':v.sku if v else vid,'quantity':int(qty or 0),
                        'sales':int(revenue or 0),'gross_margin':int(margin or 0)})
    total=sum(o.total for o in sales)
    return {'start':period_start.isoformat(),'end':period_end.isoformat(),
            'sales':total,'paid':sum(o.paid for o in sales),'orders':len(sales),
            'average_order':total//len(sales) if sales else 0,
            'daily':sorted(daily.values(),key=lambda x:x['date']),
            'channels':sorted(channels.values(),key=lambda x:-x['sales']),
            'top_products':top,'currency':'TOMAN'}

CSV_RESOURCES={'products','variants','warehouses','stocks','movements','batches',
               'suppliers','customers','purchases','purchase-lines','sales','sales-lines',
               'payments','returns','shipments','price-lists','price-items','cash-accounts',
               'account-entries','notifications','audit'}

@app.get('/api/export/{resource}.csv')
def export_resource(resource:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    if resource not in CSV_RESOURCES or resource not in READABLE:
        raise HTTPException(404,'منبع خروجی نامعتبر')
    model,roles,_=READABLE[resource]
    authorized(ctx,roles)
    # Bounded export; avoids unbounded serverless memory use.
    rows=db.query(model).filter_by(tenant_id=ctx['tenant']).order_by(
        model.created_at.desc()).limit(10000).all()
    columns=[c.name for c in model.__table__.columns]
    output=io.StringIO(newline='')
    writer=csv.writer(output)
    writer.writerow(columns)
    def excel_safe(v):
        if v is None:return ''
        txt=str(v)
        if txt and txt[0] in ('=','+','-','@','\t','\r'):
            return "'"+txt
        return txt
    for row in rows:
        writer.writerow([excel_safe(getattr(row,k)) for k in columns])
    csv_text='\ufeff'+output.getvalue()
    return StreamingResponse(iter([csv_text.encode('utf-8')]),media_type='text/csv; charset=utf-8',
                             headers={'Content-Disposition':f'attachment; filename="erp-{resource}.csv"',
                                      'Cache-Control':'no-store'})


@app.post('/api/serials/register')
def serial_register(body:dict=Body(...),db:Session=Depends(db_session),
                    ctx:dict=Depends(principal)):
    """Identify legacy on-hand serialized units without altering aggregate stock."""
    authorized(ctx,WAREHOUSE)
    wid=body.get('warehouse_id');vid=body.get('variant_id')
    tenant_object(db,Warehouse,ctx['tenant'],wid)
    var=tenant_object(db,Variant,ctx['tenant'],vid)
    if not var.track_serial:raise HTTPException(409,'ردیابی سریال برای این کالا فعال نیست')
    requested=body.get('serials')
    if (not isinstance(requested,list) or not 1<=len(requested)<=100 or
            not all(isinstance(x,str) and 0<len(x)<=150 for x in requested) or
            len(set(requested))!=len(requested)):
        raise HTTPException(422,'شماره سریال‌ها تکراری یا نامعتبر هستند')
    if db.bind.dialect.name=='postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'),{
            'key':ctx['tenant']+':'+wid+':'+vid})
    stock=db.query(Stock).filter_by(tenant_id=ctx['tenant'],warehouse_id=wid,
                variant_id=vid).with_for_update().first()
    if not stock:raise HTTPException(409,'ابتدا موجودی کالا را ثبت کنید')
    registered=db.query(SerialItem).filter_by(tenant_id=ctx['tenant'],warehouse_id=wid,
                             variant_id=vid,status='in_stock').count()
    if registered+len(requested)>stock.quantity:
        raise HTTPException(409,'تعداد سریال‌ها از موجودی ثبت‌شده بیشتر است')
    for serial in requested:
        db.add(SerialItem(tenant_id=ctx['tenant'],warehouse_id=wid,
                          variant_id=vid,serial=serial,status='in_stock'))
    audit(db,ctx,'register','serials',vid,{'count':len(requested),'warehouse_id':wid})
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'شماره سریال تکراری است')
    return {'ok':True,'registered':len(requested)}

@app.get('/api/stock/traceability/{variant_id}')
def traceability(variant_id:str,warehouse_id:str,
                 db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    authorized(ctx,ALL)
    tenant_object(db,Variant,ctx['tenant'],variant_id)
    tenant_object(db,Warehouse,ctx['tenant'],warehouse_id)
    lots=db.query(StockBatch).filter_by(tenant_id=ctx['tenant'],warehouse_id=warehouse_id,
                variant_id=variant_id).order_by(StockBatch.expiry_date.asc()).all()
    serials=db.query(SerialItem).filter_by(tenant_id=ctx['tenant'],warehouse_id=warehouse_id,
                   variant_id=variant_id).order_by(SerialItem.created_at.desc()).limit(300).all()
    return {'lots':[as_dict(x) for x in lots],
            'serials':[as_dict(x) for x in serials],
            'serial_total':db.query(SerialItem).filter_by(tenant_id=ctx['tenant'],
               warehouse_id=warehouse_id,variant_id=variant_id).count()}


@app.get('/api/auth/sessions')
def list_sessions(db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    rows=db.query(AuthSession).filter_by(user_id=ctx['user'].id,
             tenant_id=ctx['tenant']).order_by(AuthSession.created_at.desc()).limit(100).all()
    return {'items':[{'id':x.id,'created_at':x.created_at.isoformat(),
                      'expires_at':x.expires_at.isoformat(),
                      'revoked':x.revoked_at is not None} for x in rows]}

@app.post('/api/auth/sessions/{session_id}/revoke')
def revoke_session(session_id:str,db:Session=Depends(db_session),ctx:dict=Depends(principal)):
    item=db.query(AuthSession).filter_by(id=session_id,user_id=ctx['user'].id,
                 tenant_id=ctx['tenant']).with_for_update().first()
    if not item:raise HTTPException(404,'نشست موجود نیست')
    item.revoked_at=datetime.now(timezone.utc)
    db.commit()
    return {'ok':True}

@app.post('/api/auth/password/change')
def change_password(body:dict=Body(...),db:Session=Depends(db_session),
                    ctx:dict=Depends(principal)):
    old=body.get('current_password');new=body.get('new_password')
    if not isinstance(old,str) or not verify_password(old,ctx['user'].password_hash):
        raise HTTPException(403,'رمز عبور فعلی نادرست است')
    if not isinstance(new,str) or not 12<=len(new)<=200:
        raise HTTPException(422,'رمز عبور جدید باید حداقل ۱۲ نویسه باشد')
    ctx['user'].password_hash=make_password(new)
    db.query(AuthSession).filter_by(user_id=ctx['user'].id).update({
        AuthSession.revoked_at:datetime.now(timezone.utc)})
    audit(db,ctx,'password_change','users',ctx['user'].id)
    db.commit()
    response=JSONResponse({'ok':True})
    response.delete_cookie('erp_session',path='/')
    return response

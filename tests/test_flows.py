import os,tempfile
fd,path=tempfile.mkstemp(suffix='.db');os.close(fd)
os.environ['DATABASE_URL']='sqlite:///'+path
os.environ['APP_SECRET']='test-secret-only'
from fastapi.testclient import TestClient
from api.index import app

def create_user(client,label):
    r=client.post('/api/auth/register',json={'name':label,'company':f'Company {label}','email':f'{label}@example.com','password':'A-strong-test-password-999'})
    assert r.status_code==200,r.text
    return client.get('/api/auth/me').json()

def create(client,resource,**vals):
    r=client.post('/api/data/'+resource,json=vals)
    assert r.status_code==200,(resource,r.text)
    return r.json()

def test_full_flow_and_tenant_isolation():
    a=TestClient(app)
    b=TestClient(app)
    ua=create_user(a,'alice')
    ub=create_user(b,'bob')
    assert ua['tenant_id']!=ub['tenant_id']
    wh=a.get('/api/data/warehouses').json()['items'][0]
    cat=create(a,'categories',name='عطر')
    prod=create(a,'products',name='عطر نمونه',category_id=cat['id'])
    var=create(a,'variants',product_id=prod['id'],name='۵۰ میل',sku='P-001',purchase_cost=1000,retail_price=2200,wholesale_price=1800)
    supplier=create(a,'suppliers',name='تامین‌کننده')
    customer=create(a,'customers',name='مشتری آزمایشی')
    cash=a.get('/api/data/cash-accounts').json()['items'][0]
    assert a.post('/api/data/variants',json={'product_id':prod['id'],'name':'تکراری','sku':'P-001'}).status_code==409
    assert b.post('/api/data/variants',json={'product_id':prod['id'],'name':'سرقت','sku':'P-500'}).status_code==404
    assert len(b.get('/api/data/products').json()['items'])==0
    assert a.post('/api/stock/adjust',json={'warehouse_id':wh['id'],'variant_id':var['id'],'delta':-1,'reason':'loss'}).status_code==409
    adjust=a.post('/api/stock/adjust',json={'warehouse_id':wh['id'],'variant_id':var['id'],'delta':7,'reason':'opening'})
    assert adjust.status_code==200,adjust.text
    assert adjust.json()['quantity']==7
    other=create(a,'warehouses',name='انبار دوم',code='WH2')
    tr=a.post('/api/transfers',json={'source_id':wh['id'],'destination_id':other['id'],'variant_id':var['id'],'quantity':2})
    assert tr.status_code==200,tr.text
    tid=tr.json()['id']
    assert a.post(f'/api/transfers/{tid}/ship').json()['status']=='shipped'
    assert a.post(f'/api/transfers/{tid}/ship').status_code==409
    assert a.post(f'/api/transfers/{tid}/receive').json()['status']=='received'
    po=a.post('/api/purchases',json={'supplier_id':supplier['id'],'warehouse_id':wh['id'],'items':[{'variant_id':var['id'],'quantity':10,'cost':1000}]})
    assert po.status_code==200,po.text
    poid=po.json()['id']
    assert a.post(f'/api/purchases/{poid}/receive',json={}).json()['status']=='received'
    assert a.post(f'/api/purchases/{poid}/receive',json={}).status_code==409
    order=a.post('/api/sales',json={'customer_id':customer['id'],'warehouse_id':wh['id'],'items':[{'variant_id':var['id'],'quantity':3}]})
    assert order.status_code==200,order.text
    oid=order.json()['id']
    assert a.post(f'/api/sales/{oid}/confirm').json()['status']=='confirmed'
    too_big=a.post('/api/sales',json={'warehouse_id':wh['id'],'items':[{'variant_id':var['id'],'quantity':100}]})
    assert too_big.status_code==200
    assert a.post(f'/api/sales/{too_big.json()["id"]}/confirm').status_code==409
    assert a.post(f'/api/sales/{oid}/fulfill').json()['status']=='fulfilled'
    payment={'sale_id':oid,'amount':2200,'method':'cash','account_id':cash['id'],'idempotency_key':'alice-sale-payment-1'}
    assert a.post('/api/payments',json=payment).json()['duplicate']==False
    assert a.post('/api/payments',json=payment).json()['duplicate']==True
    assert a.post('/api/payments',json={**payment,'amount':2201}).status_code==409
    assert a.post('/api/payments',json={**payment,'sale_id':'different'}).status_code==409
    assert a.post('/api/payments',json={**payment,'idempotency_key':'2','amount':999999}).status_code==409
    ret=a.post('/api/returns',json={'direction':'sale','order_id':oid,'variant_id':var['id'],'quantity':2,'restock':True})
    assert ret.status_code==200,ret.text
    assert a.post('/api/returns',json={'direction':'sale','order_id':oid,'variant_id':var['id'],'quantity':2}).status_code==409
    assert a.get('/api/dashboard').json()['orders']==2
    assert len(a.get('/api/reports',params={'type':'margins'}).json()['rows'])>0
    assert b.post('/api/payments',json={'sale_id':oid,'amount':10,'idempotency_key':'cross-tenant'}).status_code==404
    assert b.get('/api/data/movements').json()['items']==[]
    assert a.get('/api/data/movements').json()['total']>=5
    assert a.post('/api/auth/logout').status_code==200
    assert a.get('/api/auth/me').status_code==401

def test_invite_rbac_and_reference_isolation():
    owner=TestClient(app);guest=TestClient(app);stranger=TestClient(app)
    a=create_user(owner,'owner-rbac')
    b=create_user(guest,'guest-rbac')
    c=create_user(stranger,'stranger-rbac')
    cat=create(owner,'categories',name='کالای مستقل')
    x=stranger.post('/api/data/categories',json={'name':'نفوذ','parent_id':cat['id']})
    assert x.status_code==404,x.text
    invite=owner.post('/api/invites',json={'email':'guest-rbac@example.com','role':'viewer'})
    assert invite.status_code==200,invite.text
    token=invite.json()['token']
    assert stranger.post('/api/auth/accept-invite',json={'token':token}).status_code==403
    ok=guest.post('/api/auth/accept-invite',json={'token':token})
    assert ok.status_code==200,ok.text
    assert guest.post('/api/auth/accept-invite',json={'token':token}).status_code==403
    assert guest.get('/api/auth/me').json()['tenant_id']==a['tenant_id']
    assert guest.get('/api/data/categories').json()['total']==1
    assert guest.post('/api/data/categories',json={'name':'غیرمجاز'}).status_code==403
    assert guest.post('/api/stock/adjust',json={'warehouse_id':'test','variant_id':'test','delta':1,'reason':'opening'}).status_code==403
    membership=next(m for m in owner.get('/api/members').json()['items'] if m['email']=='guest-rbac@example.com')
    updated=owner.patch('/api/members/'+membership['id'],json={'role':'inventory_manager','active':True})
    assert updated.status_code==200,updated.text
    assert guest.post('/api/data/categories',json={'name':'مجاز'}).status_code==200
    assert guest.post('/api/payments',json={'sale_id':'x','amount':10,'idempotency_key':'impossible'}).status_code==403
    assert stranger.get('/api/data/categories').json()['total']==0


def test_cross_origin_mutation_returns_403_not_500():
    client=TestClient(app, raise_server_exceptions=False)
    response=client.post('/api/auth/login', json={'email':'nobody@example.com','password':'test'},
                         headers={'Origin':'https://malicious.example'})
    assert response.status_code==403, response.text
    assert response.json()['detail']=='درخواست از مبدأ غیرمجاز'

def test_database_readiness():
    client=TestClient(app)
    r=client.get('/api/ready')
    assert r.status_code==200,r.text
    assert r.json()=={'ok':True,'database':'connected'}


def test_cycle_count_adjustments_and_stale_snapshot():
    client=TestClient(app)
    owner=create_user(client,'cycle-owner')
    wh=client.get('/api/data/warehouses').json()['items'][0]
    product=create(client,'products',name='کالای انبارگردانی')
    variant=create(client,'variants',product_id=product['id'],name='اصلی',sku='CYCL-0001',purchase_cost=100,retail_price=200)
    sheet=client.get('/api/stock/cycle-sheet',params={'warehouse_id':wh['id']})
    assert sheet.status_code==200,sheet.text
    assert sheet.json()['items'][0]['quantity']==0
    initial=client.post('/api/stock/adjust',json={'warehouse_id':wh['id'],'variant_id':variant['id'],'delta':10,'reason':'opening'})
    assert initial.status_code==200,initial.text
    payload={'warehouse_id':wh['id'],'idempotency_key':'cycle-first',
             'items':[{'variant_id':variant['id'],'expected_quantity':10,'counted':7}]}
    first=client.post('/api/stock/cycle-count',json=payload)
    assert first.status_code==200,first.text
    assert first.json()['items'][0]['difference']==-3
    assert client.post('/api/stock/cycle-count',json=payload).status_code==409
    stale=client.post('/api/stock/cycle-count',json={**payload,'idempotency_key':'cycle-stale'})
    assert stale.status_code==409
    assert client.get('/api/stock/cycle-sheet',params={'warehouse_id':wh['id']}).json()['items'][0]['quantity']==7
    assert client.post('/api/stock/cycle-count',json={**payload,'idempotency_key':'cycle-empty',
                'items':[{'variant_id':variant['id'],'expected_quantity':7,'counted':7}]}).status_code==200
    assert client.post('/api/stock/cycle-count',json={**payload,'idempotency_key':'cycle-negative',
                'items':[{'variant_id':variant['id'],'expected_quantity':7,'counted':-2}]}).status_code==422
    assert client.post('/api/stock/cycle-count',json={**payload,'idempotency_key':'cycle-dup',
                'items':[payload['items'][0],payload['items'][0]]}).status_code==422
    other=TestClient(app)
    create_user(other,'cycle-outsider')
    assert other.get('/api/stock/cycle-sheet',params={'warehouse_id':wh['id']}).status_code==404
    assert other.post('/api/stock/cycle-count',json=payload).status_code==404
    movements=client.get('/api/data/movements').json()['items']
    assert any(m['reason']=='cycle_count' and m['delta']==-3 for m in movements)


def test_refund_and_vendor_reimbursement_settlement():
    client=TestClient(app)
    create_user(client,'settlement-owner')
    wh=client.get('/api/data/warehouses').json()['items'][0]
    account=client.get('/api/data/cash-accounts').json()['items'][0]
    product=create(client,'products',name='کالا با مرجوعی')
    variant=create(client,'variants',product_id=product['id'],name='بسته',sku='RET-001',purchase_cost=400,retail_price=1000)
    supplier=create(client,'suppliers',name='تامین کننده تسویه')
    assert client.post('/api/stock/adjust',json={'warehouse_id':wh['id'],'variant_id':variant['id'],'delta':6,'reason':'opening'}).status_code==200
    order=client.post('/api/sales',json={'warehouse_id':wh['id'],'items':[{'variant_id':variant['id'],'quantity':2}]}).json()
    assert client.post('/api/sales/'+order['id']+'/confirm').status_code==200
    assert client.post('/api/sales/'+order['id']+'/fulfill').status_code==200
    payment={'sale_id':order['id'],'amount':1500,'account_id':account['id'],'idempotency_key':'refund-payment-1'}
    assert client.post('/api/payments',json=payment).status_code==200
    ret=client.post('/api/returns',json={'direction':'sale','order_id':order['id'],'variant_id':variant['id'],'quantity':2,'restock':True}).json()
    state=client.get('/api/returns/'+ret['id']+'/settlement')
    assert state.status_code==200,state.text
    assert state.json()['remaining']==1500
    p={'amount':700,'account_id':account['id'],'idempotency_key':'refund-1'}
    first=client.post('/api/returns/'+ret['id']+'/settle',json=p)
    assert first.status_code==200,first.text
    assert first.json()['remaining']==800
    assert client.post('/api/returns/'+ret['id']+'/settle',json=p).status_code==409
    assert client.post('/api/returns/'+ret['id']+'/settle',json={**p,'idempotency_key':'refund-too-much','amount':801}).status_code==409
    assert client.post('/api/returns/'+ret['id']+'/settle',json={**p,'idempotency_key':'refund-2','amount':800}).status_code==200
    assert client.get('/api/returns/'+ret['id']+'/settlement').json()['remaining']==0
    assert client.post('/api/returns/'+ret['id']+'/settle',json={**p,'idempotency_key':'refund-3','amount':1}).status_code==409
    po=client.post('/api/purchases',json={'supplier_id':supplier['id'],'warehouse_id':wh['id'],
                   'items':[{'variant_id':variant['id'],'quantity':3,'cost':400}]}).json()
    assert client.post('/api/purchases/'+po['id']+'/receive',json={}).status_code==200
    assert client.post('/api/payments',json={'purchase_id':po['id'],'amount':1200,
                   'account_id':account['id'],'idempotency_key':'purchase-payment-1'}).status_code==200
    purchase_return=client.post('/api/returns',json={'direction':'purchase','order_id':po['id'],'variant_id':variant['id'],'quantity':1}).json()
    assert client.get('/api/returns/'+purchase_return['id']+'/settlement').json()['remaining']==400
    assert client.post('/api/returns/'+purchase_return['id']+'/settle',json={
                   'amount':400,'account_id':account['id'],'idempotency_key':'vendor-reimburse-1'}).status_code==200
    stranger=TestClient(app)
    create_user(stranger,'settlement-stranger')
    assert stranger.get('/api/returns/'+ret['id']+'/settlement').status_code==404
    assert stranger.post('/api/returns/'+ret['id']+'/settle',json=p).status_code==404


def test_internal_invoice_snapshot_print_and_tenant_scope():
    client=TestClient(app)
    create_user(client,'invoice-owner')
    wh=client.get('/api/data/warehouses').json()['items'][0]
    product=create(client,'products',name='کالای فاکتور')
    var=create(client,'variants',product_id=product['id'],name='بسته ۱',sku='INV-SKU-1',purchase_cost=200,retail_price=800)
    assert client.post('/api/stock/adjust',json={'warehouse_id':wh['id'],'variant_id':var['id'],'delta':4,'reason':'opening'}).status_code==200
    draft=client.post('/api/sales',json={'warehouse_id':wh['id'],
           'items':[{'variant_id':var['id'],'quantity':2}], 'discount':100}).json()
    assert client.post('/api/invoices',json={'order_id':draft['id']}).status_code==409
    assert client.post('/api/sales/'+draft['id']+'/confirm').status_code==200
    issued=client.post('/api/invoices',json={'order_id':draft['id']})
    assert issued.status_code==200,issued.text
    inv=issued.json()['invoice']
    assert inv['total']==1500 and inv['discount']==100 and inv['subtotal']==1600
    assert client.post('/api/invoices',json={'order_id':draft['id']}).json()['duplicate']==True
    result=client.get('/api/invoices/'+inv['id'])
    assert result.status_code==200
    assert result.json()['items'][0]['sku_snapshot']=='INV-SKU-1'
    assert client.patch('/api/data/variants/'+var['id'],json={'name':'نام تازه','retail_price':900}).status_code==200
    immutable=client.get('/api/invoices/'+inv['id']).json()['items'][0]
    assert immutable['name_snapshot']=='بسته ۱' and immutable['price']==800
    printable=client.get('/api/invoices/'+inv['id']+'/print')
    assert printable.status_code==200 and 'INV-SKU-1' in printable.text
    assert 'فاکتور رسمی' in printable.text
    stranger=TestClient(app)
    create_user(stranger,'invoice-stranger')
    assert stranger.get('/api/invoices/'+inv['id']).status_code==404
    assert stranger.get('/api/invoices/'+inv['id']+'/print').status_code==404


def test_public_showroom_is_isolated_and_read_only(monkeypatch):
    """Anonymous showroom exposes only a dedicated synthetic tenant, never writes."""
    from api.db import Session as DbSession
    from api.models import User, Tenant, Member, Product
    from api.security import DEMO_TENANT_ID, DEMO_USER_ID
    session=DbSession()
    try:
        session.add(Tenant(id=DEMO_TENANT_ID,name='دموی آزمایشی',currency='TOMAN'))
        session.add(User(id=DEMO_USER_ID,name='بازدیدکننده',email='demo-host@example.invalid',
                         password_hash='disabled-demo-credentials',active=True))
        session.flush()
        session.add(Member(id='demo-test-member',tenant_id=DEMO_TENANT_ID,user_id=DEMO_USER_ID,role='owner',active=True))
        session.add(Product(id='demo-visible-product',tenant_id=DEMO_TENANT_ID,name='کالای نمایشی',active=True,archived=False))
        session.commit()
    finally:
        session.close()
    real=TestClient(app)
    real_user=create_user(real,'real-vs-demo')
    real_product=create(real,'products',name='کالای خصوصی')
    anonymous=TestClient(app)
    assert anonymous.get('/api/auth/me').status_code==401
    monkeypatch.setenv('PUBLIC_DEMO_ENABLED','true')
    me=anonymous.get('/api/auth/me')
    assert me.status_code==200,me.text
    assert me.json()['public_demo'] is True
    assert me.json()['tenant_id']==DEMO_TENANT_ID
    catalog=anonymous.get('/api/data/products')
    assert catalog.status_code==200,catalog.text
    ids={r['id'] for r in catalog.json()['items']}
    assert 'demo-visible-product' in ids and real_product['id'] not in ids
    assert anonymous.get('/api/members').status_code==200
    assert anonymous.get('/api/organizations').json()['items'][0]['id']==DEMO_TENANT_ID
    for method,path,body in [
        ('post','/api/data/products',{'name':'دستکاری دمو'}),
        ('patch','/api/data/products/demo-visible-product',{'name':'دستکاری دمو'}),
        ('delete','/api/data/products/demo-visible-product',None),
        ('post','/api/auth/register',{'name':'x','company':'x','email':'bad@example.invalid','password':'longpassword123'}),
        ('post','/api/stock/adjust',{'delta':1,'reason':'opening'}),
    ]:
        r=getattr(anonymous,method)(path,**({'json':body} if body is not None else {}))
        assert r.status_code==403,(method,path,r.text)
    # A real signed session still reads its own tenant and may manage its own data.
    assert real.get('/api/auth/me').json()['public_demo'] is False
    assert real.get('/api/auth/me').json()['tenant_id']==real_user['tenant_id']
    assert real.post('/api/data/products',json={'name':'دومین کالای خصوصی'}).status_code==200
    assert anonymous.get('/api/data/products').json()['total']==1


def test_double_entry_finance_posting_and_tenant_scoping():
    client=TestClient(app)
    owner=create_user(client,'ledger-owner')
    accounts=client.get('/api/ledger/accounts')
    assert accounts.status_code==200,accounts.text
    assert accounts.json()['total']>=10
    by_code={x['code']:x['id'] for x in accounts.json()['items']}
    data={'memo':'سند اصلاحی نمونه','idempotency_key':'manual-ledger-1',
          'lines':[{'account_id':by_code['1010'],'debit':2000000,'credit':0},
                   {'account_id':by_code['3000'],'debit':0,'credit':2000000}]}
    assert client.post('/api/ledger/journals',json={**data,'lines':[
          data['lines'][0],{**data['lines'][1],'credit':1999999}]}).status_code==422
    good=client.post('/api/ledger/journals',json=data)
    assert good.status_code==200,good.text
    assert good.json()['total']==2000000
    assert client.post('/api/ledger/journals',json=data).status_code==409
    accounts_before=client.get('/api/ledger/accounts').json()['total']
    assert client.post('/api/ledger/bootstrap').status_code==200
    assert client.get('/api/ledger/accounts').json()['total']==accounts_before
    warehouse=client.get('/api/data/warehouses').json()['items'][0]
    product=create(client,'products',name='کالای دفتر کل')
    variant=create(client,'variants',product_id=product['id'],name='اصلی',sku='GL-2026-1',
                   purchase_cost=2500000,retail_price=5000000)
    assert client.post('/api/stock/adjust',json={'warehouse_id':warehouse['id'],
                  'variant_id':variant['id'],'delta':4,'reason':'opening'}).status_code==200
    order=client.post('/api/sales',json={'warehouse_id':warehouse['id'],
                   'items':[{'variant_id':variant['id'],'quantity':1}]}).json()
    assert client.post('/api/sales/'+order['id']+'/confirm').status_code==200
    assert client.post('/api/sales/'+order['id']+'/fulfill').status_code==200
    pay=client.post('/api/payments',json={'sale_id':order['id'],'amount':3000000,
                      'method':'cash','idempotency_key':'ledger-payment-over-1m'})
    assert pay.status_code==200,pay.text
    trial=client.get('/api/ledger/trial-balance')
    assert trial.status_code==200,trial.text
    assert trial.json()['balanced'] is True
    assert trial.json()['total_debit']==trial.json()['total_credit']>10000000
    report=client.get('/api/ledger/profit-loss')
    assert report.status_code==200,report.text
    assert report.json()['revenue']>=5000000
    assert report.json()['net_profit']==report.json()['revenue']-report.json()['expenses']
    docs=client.get('/api/ledger/journals').json()
    assert docs['total']>=4
    journal=client.get('/api/ledger/journals/'+docs['items'][0]['id'])
    assert journal.status_code==200
    assert sum(x['debit'] for x in journal.json()['lines'])==sum(x['credit'] for x in journal.json()['lines'])
    stranger=TestClient(app)
    create_user(stranger,'ledger-outsider')
    assert stranger.get('/api/ledger/journals/'+docs['items'][0]['id']).status_code==404
    assert stranger.post('/api/ledger/journals',json={**data,
          'idempotency_key':'outsider', 'lines':data['lines']}).status_code==404


def test_external_adapters_off_analytics_expiry_and_csv_safety():
    from datetime import date,timedelta
    from api.db import Session as DbSession
    from api.models import StockBatch
    user=TestClient(app)
    person=create_user(user,'reports-admin')
    links=user.get('/api/integrations')
    assert links.status_code==200,links.text
    assert len(links.json()['items'])==6
    assert all(x['enabled'] is False for x in links.json()['items'])
    configured=user.put('/api/integrations/sms',json={'provider':'kavenegar',
                     'settings':{'sender':'my-test-sender'}})
    assert configured.status_code==200,configured.text
    assert configured.json()['enabled'] is False
    assert user.put('/api/integrations/sms',json={'provider':'kavenegar',
                 'settings':{'api_key':'SECRET-NOT-ALLOWED'}}).status_code==422
    assert user.post('/api/integrations/sms/activate',json={}).status_code==501
    assert user.put('/api/integrations/storage',json={'provider':'minio',
           'settings':{'endpoint':'http://not-https.example'}}).status_code==422
    wh=user.get('/api/data/warehouses').json()['items'][0]
    product=create(user,'products',name='=2+2')
    variant=create(user,'variants',product_id=product['id'],
                   name='انقضا',sku='ANALYTIC-001',purchase_cost=10000,
                   retail_price=20000)
    db=DbSession()
    try:
        db.add(StockBatch(tenant_id=person['tenant_id'],warehouse_id=wh['id'],
               variant_id=variant['id'],lot='LOT-EXPIRE',quantity=4,
               expiry_date=date.today()+timedelta(days=5)))
        db.commit()
    finally:db.close()
    ex=user.get('/api/stock/expiry-alerts?days=10')
    assert ex.status_code==200,ex.text
    assert ex.json()['total']>=1
    assert any(x['lot']=='LOT-EXPIRE' for x in ex.json()['items'])
    assert user.get('/api/stock/expiry-alerts?days=-5').status_code==422
    sale=user.post('/api/sales',json={'warehouse_id':wh['id'],
         'items':[{'variant_id':variant['id'],'quantity':2}]})
    assert sale.status_code==200,sale.text
    assert user.post('/api/stock/adjust',json={'warehouse_id':wh['id'],
           'variant_id':variant['id'],'delta':10,'reason':'opening'}).status_code==200
    assert user.post('/api/sales/'+sale.json()['id']+'/confirm').status_code==200
    analytics=user.get('/api/analytics')
    assert analytics.status_code==200,analytics.text
    assert analytics.json()['orders']>=1
    assert analytics.json()['sales']>=40000
    assert user.get('/api/analytics?start=2020-01-01&end=2026-01-01').status_code==422
    csvfile=user.get('/api/export/products.csv')
    assert csvfile.status_code==200,csvfile.text
    assert 'text/csv' in csvfile.headers['content-type']
    assert "'=2+2" in csvfile.text
    assert 'erp-products.csv' in csvfile.headers['content-disposition']
    outsider=TestClient(app)
    create_user(outsider,'reports-isolated')
    assert outsider.get('/api/analytics').json()['orders']==0
    assert outsider.get('/api/stock/expiry-alerts?days=10').json()['total']==0
    assert '=2+2' not in outsider.get('/api/export/products.csv').text

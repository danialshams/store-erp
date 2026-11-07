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

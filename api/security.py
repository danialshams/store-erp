"""Password hashing, authenticated cookies, role gates and request CSRF guard."""
import os, secrets, hmac, hashlib, time, base64, json
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from .models import User, Member

SECRET=os.environ.get('APP_SECRET', '')
if not SECRET:
    if os.environ.get('VERCEL') or os.environ.get('APP_ENV') == 'production' or os.environ.get('DATABASE_URL', '').startswith(('postgres:', 'postgresql:')):
        raise RuntimeError('APP_SECRET is required for deployed or PostgreSQL installations')
    SECRET='dev-only-not-for-production'
if (os.environ.get('VERCEL') or os.environ.get('APP_ENV') == 'production' or os.environ.get('DATABASE_URL', '').startswith(('postgres:', 'postgresql:'))) and (len(SECRET) < 32 or SECRET.startswith('replace-with')):
    raise RuntimeError('APP_SECRET must be a securely generated value of at least 32 characters')
ROLES=['owner','admin','inventory_manager','sales','accountant','viewer']
ALL=set(ROLES)
CATALOG={'owner','admin','inventory_manager'}
WAREHOUSE={'owner','admin','inventory_manager'}
SALES={'owner','admin','sales'}
FINANCE={'owner','admin','accountant'}
PURCHASE={'owner','admin','inventory_manager','accountant'}

def make_password(pwd: str) -> str:
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256',pwd.encode(),salt,600_000)
    return 'pbkdf2_sha256$600000$'+salt.hex()+'$'+digest.hex()

def verify_password(pwd: str, stored: str) -> bool:
    try:
        a,iter_s,salt_hex,digest_hex=stored.split('$')
        if a!='pbkdf2_sha256': return False
        return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',pwd.encode(),bytes.fromhex(salt_hex),int(iter_s)),bytes.fromhex(digest_hex))
    except Exception:return False

def _b64(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
def _unb64(s): return base64.urlsafe_b64decode(s+'='*(-len(s)%4))

def issue_token(user_id, tenant_id):
    payload=_b64(json.dumps({'u':user_id,'t':tenant_id,'exp':int(time.time())+604800},separators=(',',':')).encode())
    sign=_b64(hmac.new(SECRET.encode(),payload.encode(),hashlib.sha256).digest())
    return payload+'.'+sign

def parse_token(token):
    try:
        a,b=token.split('.',1)
        expected=_b64(hmac.new(SECRET.encode(),a.encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(b,expected): return None
        obj=json.loads(_unb64(a))
        return obj if int(obj['exp']) > time.time() else None
    except Exception:return None

def context(request:Request,db:Session):
    auth=request.cookies.get('erp_session')
    if not auth: raise HTTPException(401,'ابتدا وارد شوید')
    claims=parse_token(auth)
    if not claims: raise HTTPException(401,'نشست منقضی شده است')
    user=db.get(User,claims['u'])
    if not user or not user.active:raise HTTPException(401,'حساب غیرفعال است')
    member=db.query(Member).filter_by(user_id=user.id,tenant_id=claims['t'],active=True).first()
    if not member:raise HTTPException(403,'دسترسی به این سازمان ندارید')
    return {'user':user,'tenant':member.tenant_id,'role':member.role}

def authorized(ctx,roles):
    if ctx['role'] not in roles: raise HTTPException(403,'اجازه انجام این عملیات را ندارید')

def csrf_guard(request: Request):
    if request.method in ('POST','PATCH','PUT','DELETE'):
        # Browsers supply Fetch Metadata even when Origin is omitted. Reject
        # cross-site mutations before session-cookie authentication.
        site=request.headers.get('sec-fetch-site', '').lower()
        if site == 'cross-site':
            raise HTTPException(403,'درخواست از مبدأ غیرمجاز')
        origin=request.headers.get('origin')
        if origin:
            host=request.headers.get('host','')
            from urllib.parse import urlparse
            o=urlparse(origin)
            expected_scheme=request.url.scheme
            # Reverse proxies may terminate TLS before reaching ASGI.
            forwarded=request.headers.get('x-forwarded-proto','').split(',')[0].strip()
            if forwarded in ('http','https'): expected_scheme=forwarded
            if o.netloc != host or o.scheme != expected_scheme:
                raise HTTPException(403,'درخواست از مبدأ غیرمجاز')
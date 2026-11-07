"""Database engine and transaction boundaries; DATABASE_URL is required on Vercel."""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL=os.environ.get('DATABASE_URL', 'sqlite:///./erp_local.db')
if os.environ.get('VERCEL') and not os.environ.get('DATABASE_URL'):
    raise RuntimeError('DATABASE_URL is required in deployment; refusing ephemeral SQLite')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL='postgresql://'+DATABASE_URL[len('postgres://'):]
engine=create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite:') else {})
Session=sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(engine)
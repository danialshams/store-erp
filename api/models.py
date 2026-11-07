"""SQLAlchemy data model: monetary fields are integer Toman; UUIDs remain portable.

All tenant-owned entities use tenant_id. API derives it exclusively from the signed
session, and privileged workflow mutations are the only stock ledger writers.
"""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index, Text, JSON, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass

class Entity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('tenants.id', ondelete='RESTRICT'), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)

class Tenant(Base):
    __tablename__='tenants'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str]=mapped_column(String(200), nullable=False)
    phone: Mapped[str|None]=mapped_column(String(30))
    address: Mapped[str|None]=mapped_column(Text)
    currency: Mapped[str]=mapped_column(String(8), default='TOMAN')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class User(Base):
    __tablename__='users'
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str]=mapped_column(String(120), nullable=False)
    email: Mapped[str]=mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[str]=mapped_column(String(300), nullable=False)
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Member(Entity,Base):
    __tablename__='members'
    user_id: Mapped[str]=mapped_column(String(36), ForeignKey('users.id'), nullable=False)
    role: Mapped[str]=mapped_column(String(30), nullable=False, default='viewer')
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    __table_args__=(UniqueConstraint('tenant_id','user_id'),)

class Category(Entity,Base):
    __tablename__='categories'
    name: Mapped[str]=mapped_column(String(180), nullable=False)
    parent_id: Mapped[str|None]=mapped_column(String(36), ForeignKey('categories.id'))
    __table_args__=(UniqueConstraint('tenant_id','name'),)

class Product(Entity,Base):
    __tablename__='products'
    name: Mapped[str]=mapped_column(String(255), nullable=False)
    category_id: Mapped[str|None]=mapped_column(String(36), ForeignKey('categories.id'))
    description: Mapped[str|None]=mapped_column(Text)
    image_url: Mapped[str|None]=mapped_column(Text)
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    archived: Mapped[bool]=mapped_column(Boolean, default=False)

class Variant(Entity,Base):
    __tablename__='variants'
    product_id: Mapped[str]=mapped_column(String(36), ForeignKey('products.id'), nullable=False)
    name: Mapped[str]=mapped_column(String(200), default='اصلی')
    sku: Mapped[str]=mapped_column(String(90), nullable=False)
    barcode: Mapped[str|None]=mapped_column(String(100))
    unit: Mapped[str]=mapped_column(String(30), default='عدد')
    purchase_cost: Mapped[int]=mapped_column(BigInteger, default=0)
    retail_price: Mapped[int]=mapped_column(BigInteger, default=0)
    wholesale_price: Mapped[int]=mapped_column(BigInteger, default=0)
    low_stock: Mapped[int]=mapped_column(Integer, default=5)
    track_batch: Mapped[bool]=mapped_column(Boolean, default=False)
    track_serial: Mapped[bool]=mapped_column(Boolean, default=False)
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    __table_args__=(UniqueConstraint('tenant_id','sku'),CheckConstraint('purchase_cost >= 0 AND retail_price >= 0 AND wholesale_price >= 0 AND low_stock >= 0'))

class Warehouse(Entity,Base):
    __tablename__='warehouses'
    name: Mapped[str]=mapped_column(String(180), nullable=False)
    code: Mapped[str]=mapped_column(String(40),nullable=False)
    address: Mapped[str|None]=mapped_column(Text)
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    __table_args__=(UniqueConstraint('tenant_id','code'),)

class Stock(Entity,Base):
    __tablename__='stocks'
    warehouse_id: Mapped[str]=mapped_column(String(36),ForeignKey('warehouses.id'), nullable=False)
    variant_id: Mapped[str]=mapped_column(String(36),ForeignKey('variants.id'),nullable=False)
    quantity: Mapped[int]=mapped_column(Integer,default=0)
    reserved: Mapped[int]=mapped_column(Integer,default=0)
    __table_args__=(UniqueConstraint('tenant_id','warehouse_id','variant_id'),CheckConstraint('quantity >= 0 AND reserved >= 0 AND quantity >= reserved'))

class Movement(Entity,Base):
    __tablename__='movements'
    warehouse_id: Mapped[str]=mapped_column(String(36),ForeignKey('warehouses.id'),nullable=False)
    variant_id: Mapped[str]=mapped_column(String(36),ForeignKey('variants.id'),nullable=False)
    delta: Mapped[int]=mapped_column(Integer,nullable=False)
    reason: Mapped[str]=mapped_column(String(40),nullable=False)
    reference_id: Mapped[str|None]=mapped_column(String(36))
    note: Mapped[str|None]=mapped_column(Text)
    actor_id: Mapped[str|None]=mapped_column(String(36),ForeignKey('users.id'))
    __table_args__=(CheckConstraint('delta <> 0'),)

class StockBatch(Entity,Base):
    __tablename__='stock_batches'
    warehouse_id: Mapped[str]=mapped_column(String(36), ForeignKey('warehouses.id'))
    variant_id: Mapped[str]=mapped_column(String(36), ForeignKey('variants.id'))
    lot: Mapped[str]=mapped_column(String(100))
    expiry_date: Mapped[datetime|None]=mapped_column(Date)
    quantity: Mapped[int]=mapped_column(Integer,default=0)
    __table_args__=(UniqueConstraint('tenant_id','warehouse_id','variant_id','lot'),CheckConstraint('quantity >= 0'))

class Transfer(Entity,Base):
    __tablename__='transfers'
    source_id: Mapped[str]=mapped_column(String(36),ForeignKey('warehouses.id'),nullable=False)
    destination_id: Mapped[str]=mapped_column(String(36),ForeignKey('warehouses.id'),nullable=False)
    variant_id: Mapped[str]=mapped_column(String(36),ForeignKey('variants.id'),nullable=False)
    quantity: Mapped[int]=mapped_column(Integer,nullable=False)
    status: Mapped[str]=mapped_column(String(24),default='draft')
    actor_id: Mapped[str]=mapped_column(String(36),ForeignKey('users.id'))
    __table_args__=(CheckConstraint('quantity > 0'),CheckConstraint('source_id <> destination_id'))

class Supplier(Entity,Base):
    __tablename__='suppliers'
    name: Mapped[str]=mapped_column(String(200),nullable=False)
    phone: Mapped[str|None]=mapped_column(String(30))
    email: Mapped[str|None]=mapped_column(String(254))
    address: Mapped[str|None]=mapped_column(Text)
    notes: Mapped[str|None]=mapped_column(Text)

class Customer(Entity,Base):
    __tablename__='customers'
    name: Mapped[str]=mapped_column(String(200),nullable=False)
    phone: Mapped[str|None]=mapped_column(String(30))
    email: Mapped[str|None]=mapped_column(String(254))
    address: Mapped[str|None]=mapped_column(Text)
    group_name: Mapped[str]=mapped_column(String(80),default='عادی')
    credit_limit: Mapped[int]=mapped_column(BigInteger,default=0)
    __table_args__=(CheckConstraint('credit_limit >= 0'),)

class PurchaseOrder(Entity,Base):
    __tablename__='purchase_orders'
    supplier_id: Mapped[str]=mapped_column(String(36),ForeignKey('suppliers.id'),nullable=False)
    warehouse_id: Mapped[str]=mapped_column(String(36),ForeignKey('warehouses.id'),nullable=False)
    number: Mapped[str]=mapped_column(String(50),nullable=False)
    status: Mapped[str]=mapped_column(String(24),default='draft')
    total: Mapped[int]=mapped_column(BigInteger,default=0)
    paid: Mapped[int]=mapped_column(BigInteger,default=0)
    __table_args__=(UniqueConstraint('tenant_id','number'),CheckConstraint('total >= 0 AND paid >= 0 AND paid <= total'))

class PurchaseLine(Entity,Base):
    __tablename__='purchase_lines'
    order_id: Mapped[str]=mapped_column(String(36),ForeignKey('purchase_orders.id'),nullable=False)
    variant_id: Mapped[str]=mapped_column(String(36),ForeignKey('variants.id'),nullable=False)
    quantity: Mapped[int]=mapped_column(Integer,nullable=False)
    received: Mapped[int]=mapped_column(Integer,default=0)
    cost: Mapped[int]=mapped_column(BigInteger,nullable=False)
    __table_args__=(CheckConstraint('quantity > 0 AND received >= 0 AND received <= quantity AND cost >= 0'),)

class SalesOrder(Entity,Base):
    __tablename__='sales_orders'
    customer_id: Mapped[str|None]=mapped_column(String(36),ForeignKey('customers.id'))
    warehouse_id: Mapped[str]=mapped_column(String(36),ForeignKey('warehouses.id'),nullable=False)
    number: Mapped[str]=mapped_column(String(50),nullable=False)
    channel: Mapped[str]=mapped_column(String(25),default='retail')
    status: Mapped[str]=mapped_column(String(24),default='draft')
    total: Mapped[int]=mapped_column(BigInteger,default=0)
    paid: Mapped[int]=mapped_column(BigInteger,default=0)
    discount: Mapped[int]=mapped_column(BigInteger,default=0)
    __table_args__=(UniqueConstraint('tenant_id','number'),CheckConstraint('total >= 0 AND paid >= 0 AND paid <= total AND discount >= 0'))

class SalesLine(Entity,Base):
    __tablename__='sales_lines'
    order_id: Mapped[str]=mapped_column(String(36),ForeignKey('sales_orders.id'),nullable=False)
    variant_id: Mapped[str]=mapped_column(String(36),ForeignKey('variants.id'),nullable=False)
    quantity: Mapped[int]=mapped_column(Integer,nullable=False)
    returned: Mapped[int]=mapped_column(Integer,default=0)
    price: Mapped[int]=mapped_column(BigInteger,nullable=False)
    cost_snapshot: Mapped[int]=mapped_column(BigInteger,default=0)
    __table_args__=(CheckConstraint('quantity > 0 AND price >= 0 AND returned >= 0 AND returned <= quantity'),)

class Payment(Entity,Base):
    __tablename__='payments'
    order_id: Mapped[str|None]=mapped_column(String(36),ForeignKey('sales_orders.id'))
    purchase_id: Mapped[str|None]=mapped_column(String(36),ForeignKey('purchase_orders.id'))
    amount: Mapped[int]=mapped_column(BigInteger,nullable=False)
    method: Mapped[str]=mapped_column(String(40),default='cash')
    idempotency_key: Mapped[str]=mapped_column(String(120),nullable=False)
    actor_id: Mapped[str]=mapped_column(String(36),ForeignKey('users.id'))
    __table_args__=(UniqueConstraint('tenant_id','idempotency_key'),CheckConstraint('amount > 0'))

class Return(Entity,Base):
    __tablename__='returns'
    order_id: Mapped[str|None]=mapped_column(String(36),ForeignKey('sales_orders.id'))
    purchase_id: Mapped[str|None]=mapped_column(String(36),ForeignKey('purchase_orders.id'))
    variant_id: Mapped[str]=mapped_column(String(36),ForeignKey('variants.id'),nullable=False)
    warehouse_id: Mapped[str]=mapped_column(String(36),ForeignKey('warehouses.id'),nullable=False)
    quantity: Mapped[int]=mapped_column(Integer,nullable=False)
    amount: Mapped[int]=mapped_column(BigInteger,default=0)
    direction: Mapped[str]=mapped_column(String(24),nullable=False)
    restock: Mapped[bool]=mapped_column(Boolean,default=True)
    __table_args__=(CheckConstraint('quantity > 0 AND amount >= 0'),)

class Shipment(Entity,Base):
    __tablename__='shipments'
    order_id: Mapped[str]=mapped_column(String(36),ForeignKey('sales_orders.id'),nullable=False)
    carrier: Mapped[str|None]=mapped_column(String(100))
    tracking_number: Mapped[str|None]=mapped_column(String(100))
    status: Mapped[str]=mapped_column(String(24),default='pending')
    address: Mapped[str|None]=mapped_column(Text)

class PriceList(Entity,Base):
    __tablename__='price_lists'
    name: Mapped[str]=mapped_column(String(180),nullable=False)
    group_name: Mapped[str|None]=mapped_column(String(80))
    active: Mapped[bool]=mapped_column(Boolean,default=True)

class PriceItem(Entity,Base):
    __tablename__='price_items'
    list_id: Mapped[str]=mapped_column(String(36),ForeignKey('price_lists.id'),nullable=False)
    variant_id: Mapped[str]=mapped_column(String(36),ForeignKey('variants.id'),nullable=False)
    price: Mapped[int]=mapped_column(BigInteger,nullable=False)
    __table_args__=(UniqueConstraint('tenant_id','list_id','variant_id'),CheckConstraint('price >= 0'))

class CashAccount(Entity,Base):
    __tablename__='cash_accounts'
    name: Mapped[str]=mapped_column(String(160),nullable=False)
    type: Mapped[str]=mapped_column(String(25),default='cash')
    opening_balance: Mapped[int]=mapped_column(BigInteger,default=0)

class AccountEntry(Entity,Base):
    __tablename__='account_entries'
    account_id: Mapped[str]=mapped_column(String(36),ForeignKey('cash_accounts.id'),nullable=False)
    direction: Mapped[str]=mapped_column(String(12),nullable=False)
    amount: Mapped[int]=mapped_column(BigInteger,nullable=False)
    reference: Mapped[str|None]=mapped_column(String(36))
    note: Mapped[str|None]=mapped_column(Text)
    __table_args__=(CheckConstraint('amount > 0'),)

class Tax(Entity,Base):
    __tablename__='tax_rates'
    name: Mapped[str]=mapped_column(String(100),nullable=False)
    percentage: Mapped[int]=mapped_column(Integer,default=0)
    __table_args__=(CheckConstraint('percentage >= 0 AND percentage <= 100'),)

class Notification(Entity,Base):
    __tablename__='notifications'
    title: Mapped[str]=mapped_column(String(240),nullable=False)
    body: Mapped[str|None]=mapped_column(Text)
    category: Mapped[str]=mapped_column(String(40),default='info')
    read: Mapped[bool]=mapped_column(Boolean,default=False)

class Audit(Entity,Base):
    __tablename__='audit_logs'
    actor_id: Mapped[str|None]=mapped_column(String(36),ForeignKey('users.id'))
    action: Mapped[str]=mapped_column(String(80),nullable=False)
    entity: Mapped[str]=mapped_column(String(80),nullable=False)
    entity_id: Mapped[str|None]=mapped_column(String(36))
    details: Mapped[dict]=mapped_column(JSON,default=dict)

class Sequence(Entity,Base):
    __tablename__='sequences'
    key: Mapped[str]=mapped_column(String(40),nullable=False)
    next_value: Mapped[int]=mapped_column(Integer,default=1)
    __table_args__=(UniqueConstraint('tenant_id','key'),)

Index('idx_sales_date', SalesOrder.tenant_id, SalesOrder.created_at)
Index('idx_movements_date', Movement.tenant_id, Movement.created_at)

class EventKey(Entity,Base):
    __tablename__='event_keys'
    kind: Mapped[str]=mapped_column(String(60),nullable=False)
    key: Mapped[str]=mapped_column(String(150),nullable=False)
    reference_id: Mapped[str|None]=mapped_column(String(36))
    __table_args__=(UniqueConstraint('tenant_id','kind','key'),)

class Invite(Entity,Base):
    __tablename__='invites'
    email: Mapped[str]=mapped_column(String(254),nullable=False)
    role: Mapped[str]=mapped_column(String(30),nullable=False)
    token_hash: Mapped[str]=mapped_column(String(64),nullable=False,unique=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
    used_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
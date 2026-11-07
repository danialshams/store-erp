-- ERP Store, migration 0001: PostgreSQL 14+

-- Run with psql -v ON_ERROR_STOP=1 -f migrations/0001_schema.sql

BEGIN;


CREATE TABLE tenants (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	phone VARCHAR(30), 
	address TEXT, 
	currency VARCHAR(8) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE users (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(300) NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
)

;


CREATE TABLE audit_logs (
	actor_id VARCHAR(36), 
	action VARCHAR(80) NOT NULL, 
	entity VARCHAR(80) NOT NULL, 
	entity_id VARCHAR(36), 
	details JSON NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE cash_accounts (
	name VARCHAR(160) NOT NULL, 
	type VARCHAR(25) NOT NULL, 
	opening_balance BIGINT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE categories (
	name VARCHAR(180) NOT NULL, 
	parent_id VARCHAR(36), 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, name), 
	FOREIGN KEY(parent_id) REFERENCES categories (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE customers (
	name VARCHAR(200) NOT NULL, 
	phone VARCHAR(30), 
	email VARCHAR(254), 
	address TEXT, 
	group_name VARCHAR(80) NOT NULL, 
	credit_limit BIGINT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (credit_limit >= 0), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE event_keys (
	kind VARCHAR(60) NOT NULL, 
	key VARCHAR(150) NOT NULL, 
	reference_id VARCHAR(36), 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, kind, key), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE invites (
	email VARCHAR(254) NOT NULL, 
	role VARCHAR(30) NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	used_at TIMESTAMP WITH TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (token_hash), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE members (
	user_id VARCHAR(36) NOT NULL, 
	role VARCHAR(30) NOT NULL, 
	active BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE notifications (
	title VARCHAR(240) NOT NULL, 
	body TEXT, 
	category VARCHAR(40) NOT NULL, 
	read BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE price_lists (
	name VARCHAR(180) NOT NULL, 
	group_name VARCHAR(80), 
	active BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE sequences (
	key VARCHAR(40) NOT NULL, 
	next_value INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, key), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE suppliers (
	name VARCHAR(200) NOT NULL, 
	phone VARCHAR(30), 
	email VARCHAR(254), 
	address TEXT, 
	notes TEXT, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE tax_rates (
	name VARCHAR(100) NOT NULL, 
	percentage INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (percentage >= 0 AND percentage <= 100), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE warehouses (
	name VARCHAR(180) NOT NULL, 
	code VARCHAR(40) NOT NULL, 
	address TEXT, 
	active BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, code), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE account_entries (
	account_id VARCHAR(36) NOT NULL, 
	direction VARCHAR(12) NOT NULL, 
	amount BIGINT NOT NULL, 
	reference VARCHAR(36), 
	note TEXT, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (amount > 0), 
	FOREIGN KEY(account_id) REFERENCES cash_accounts (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE products (
	name VARCHAR(255) NOT NULL, 
	category_id VARCHAR(36), 
	description TEXT, 
	image_url TEXT, 
	active BOOLEAN NOT NULL, 
	archived BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE purchase_orders (
	supplier_id VARCHAR(36) NOT NULL, 
	warehouse_id VARCHAR(36) NOT NULL, 
	number VARCHAR(50) NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	total BIGINT NOT NULL, 
	paid BIGINT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, number), 
	CHECK (total >= 0 AND paid >= 0 AND paid <= total), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE sales_orders (
	customer_id VARCHAR(36), 
	warehouse_id VARCHAR(36) NOT NULL, 
	number VARCHAR(50) NOT NULL, 
	channel VARCHAR(25) NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	total BIGINT NOT NULL, 
	paid BIGINT NOT NULL, 
	discount BIGINT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, number), 
	CHECK (total >= 0 AND paid >= 0 AND paid <= total AND discount >= 0), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE payments (
	order_id VARCHAR(36), 
	purchase_id VARCHAR(36), 
	amount BIGINT NOT NULL, 
	method VARCHAR(40) NOT NULL, 
	idempotency_key VARCHAR(120) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, idempotency_key), 
	CHECK (amount > 0), 
	FOREIGN KEY(order_id) REFERENCES sales_orders (id), 
	FOREIGN KEY(purchase_id) REFERENCES purchase_orders (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE shipments (
	order_id VARCHAR(36) NOT NULL, 
	carrier VARCHAR(100), 
	tracking_number VARCHAR(100), 
	status VARCHAR(24) NOT NULL, 
	address TEXT, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES sales_orders (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE variants (
	product_id VARCHAR(36) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	sku VARCHAR(90) NOT NULL, 
	barcode VARCHAR(100), 
	unit VARCHAR(30) NOT NULL, 
	purchase_cost BIGINT NOT NULL, 
	retail_price BIGINT NOT NULL, 
	wholesale_price BIGINT NOT NULL, 
	low_stock INTEGER NOT NULL, 
	track_batch BOOLEAN NOT NULL, 
	track_serial BOOLEAN NOT NULL, 
	active BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, sku), 
	CHECK (purchase_cost >= 0 AND retail_price >= 0 AND wholesale_price >= 0 AND low_stock >= 0), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE movements (
	warehouse_id VARCHAR(36) NOT NULL, 
	variant_id VARCHAR(36) NOT NULL, 
	delta INTEGER NOT NULL, 
	reason VARCHAR(40) NOT NULL, 
	reference_id VARCHAR(36), 
	note TEXT, 
	actor_id VARCHAR(36), 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (delta <> 0), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(variant_id) REFERENCES variants (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE price_items (
	list_id VARCHAR(36) NOT NULL, 
	variant_id VARCHAR(36) NOT NULL, 
	price BIGINT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, list_id, variant_id), 
	CHECK (price >= 0), 
	FOREIGN KEY(list_id) REFERENCES price_lists (id), 
	FOREIGN KEY(variant_id) REFERENCES variants (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE purchase_lines (
	order_id VARCHAR(36) NOT NULL, 
	variant_id VARCHAR(36) NOT NULL, 
	quantity INTEGER NOT NULL, 
	received INTEGER NOT NULL, 
	cost BIGINT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (quantity > 0 AND received >= 0 AND received <= quantity AND cost >= 0), 
	FOREIGN KEY(order_id) REFERENCES purchase_orders (id), 
	FOREIGN KEY(variant_id) REFERENCES variants (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE returns (
	order_id VARCHAR(36), 
	purchase_id VARCHAR(36), 
	variant_id VARCHAR(36) NOT NULL, 
	warehouse_id VARCHAR(36) NOT NULL, 
	quantity INTEGER NOT NULL, 
	amount BIGINT NOT NULL, 
	direction VARCHAR(24) NOT NULL, 
	restock BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (quantity > 0 AND amount >= 0), 
	FOREIGN KEY(order_id) REFERENCES sales_orders (id), 
	FOREIGN KEY(purchase_id) REFERENCES purchase_orders (id), 
	FOREIGN KEY(variant_id) REFERENCES variants (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE sales_lines (
	order_id VARCHAR(36) NOT NULL, 
	variant_id VARCHAR(36) NOT NULL, 
	quantity INTEGER NOT NULL, 
	returned INTEGER NOT NULL, 
	price BIGINT NOT NULL, 
	cost_snapshot BIGINT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (quantity > 0 AND price >= 0 AND returned >= 0 AND returned <= quantity), 
	FOREIGN KEY(order_id) REFERENCES sales_orders (id), 
	FOREIGN KEY(variant_id) REFERENCES variants (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE stock_batches (
	warehouse_id VARCHAR(36) NOT NULL, 
	variant_id VARCHAR(36) NOT NULL, 
	lot VARCHAR(100) NOT NULL, 
	expiry_date DATE, 
	quantity INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, warehouse_id, variant_id, lot), 
	CHECK (quantity >= 0), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(variant_id) REFERENCES variants (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE stocks (
	warehouse_id VARCHAR(36) NOT NULL, 
	variant_id VARCHAR(36) NOT NULL, 
	quantity INTEGER NOT NULL, 
	reserved INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tenant_id, warehouse_id, variant_id), 
	CHECK (quantity >= 0 AND reserved >= 0 AND quantity >= reserved), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(variant_id) REFERENCES variants (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;


CREATE TABLE transfers (
	source_id VARCHAR(36) NOT NULL, 
	destination_id VARCHAR(36) NOT NULL, 
	variant_id VARCHAR(36) NOT NULL, 
	quantity INTEGER NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	tenant_id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (quantity > 0), 
	CHECK (source_id <> destination_id), 
	FOREIGN KEY(source_id) REFERENCES warehouses (id), 
	FOREIGN KEY(destination_id) REFERENCES warehouses (id), 
	FOREIGN KEY(variant_id) REFERENCES variants (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_audit_logs_tenant_id ON audit_logs (tenant_id);

CREATE INDEX ix_cash_accounts_tenant_id ON cash_accounts (tenant_id);

CREATE INDEX ix_categories_tenant_id ON categories (tenant_id);

CREATE INDEX ix_customers_tenant_id ON customers (tenant_id);

CREATE INDEX ix_event_keys_tenant_id ON event_keys (tenant_id);

CREATE INDEX ix_invites_tenant_id ON invites (tenant_id);

CREATE INDEX ix_members_tenant_id ON members (tenant_id);

CREATE INDEX ix_notifications_tenant_id ON notifications (tenant_id);

CREATE INDEX ix_price_lists_tenant_id ON price_lists (tenant_id);

CREATE INDEX ix_sequences_tenant_id ON sequences (tenant_id);

CREATE INDEX ix_suppliers_tenant_id ON suppliers (tenant_id);

CREATE INDEX ix_tax_rates_tenant_id ON tax_rates (tenant_id);

CREATE INDEX ix_warehouses_tenant_id ON warehouses (tenant_id);

CREATE INDEX ix_account_entries_tenant_id ON account_entries (tenant_id);

CREATE INDEX ix_products_tenant_id ON products (tenant_id);

CREATE INDEX ix_purchase_orders_tenant_id ON purchase_orders (tenant_id);

CREATE INDEX ix_sales_orders_tenant_id ON sales_orders (tenant_id);

CREATE INDEX idx_sales_date ON sales_orders (tenant_id, created_at);

CREATE INDEX ix_payments_tenant_id ON payments (tenant_id);

CREATE INDEX ix_shipments_tenant_id ON shipments (tenant_id);

CREATE INDEX ix_variants_tenant_id ON variants (tenant_id);

CREATE INDEX ix_movements_tenant_id ON movements (tenant_id);

CREATE INDEX idx_movements_date ON movements (tenant_id, created_at);

CREATE INDEX ix_price_items_tenant_id ON price_items (tenant_id);

CREATE INDEX ix_purchase_lines_tenant_id ON purchase_lines (tenant_id);

CREATE INDEX ix_returns_tenant_id ON returns (tenant_id);

CREATE INDEX ix_sales_lines_tenant_id ON sales_lines (tenant_id);

CREATE INDEX ix_stock_batches_tenant_id ON stock_batches (tenant_id);

CREATE INDEX ix_stocks_tenant_id ON stocks (tenant_id);

CREATE INDEX ix_transfers_tenant_id ON transfers (tenant_id);

COMMIT;
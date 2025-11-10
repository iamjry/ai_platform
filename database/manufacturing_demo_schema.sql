-- Manufacturing Demo Database Schema
-- 製造業訂單管理系統範例資料庫
-- Created: 2025-11-10

-- ==================== 客戶資料表 ====================
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_code VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT '台灣',
    credit_limit DECIMAL(15, 2) DEFAULT 0,
    payment_terms VARCHAR(50) DEFAULT 'NET30',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE customers IS '客戶資料表';
COMMENT ON COLUMN customers.customer_code IS '客戶代碼';
COMMENT ON COLUMN customers.credit_limit IS '信用額度';
COMMENT ON COLUMN customers.payment_terms IS '付款條件（如 NET30, NET60）';

-- ==================== 產品資料表 ====================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    unit VARCHAR(50) DEFAULT 'PCS',
    unit_price DECIMAL(15, 2) NOT NULL,
    standard_cost DECIMAL(15, 2),
    stock_quantity INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 10,
    lead_time_days INTEGER DEFAULT 7,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE products IS '產品資料表';
COMMENT ON COLUMN products.product_code IS '產品代碼';
COMMENT ON COLUMN products.unit IS '單位（PCS-件, SET-組, KG-公斤）';
COMMENT ON COLUMN products.unit_price IS '單價';
COMMENT ON COLUMN products.standard_cost IS '標準成本';
COMMENT ON COLUMN products.reorder_point IS '再訂購點';
COMMENT ON COLUMN products.lead_time_days IS '前置時間（天）';

-- ==================== 訂單主檔表 ====================
CREATE TABLE IF NOT EXISTS sales_orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    order_date DATE NOT NULL,
    required_date DATE,
    shipped_date DATE,
    delivery_address TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    payment_status VARCHAR(50) DEFAULT 'unpaid',
    total_amount DECIMAL(15, 2) DEFAULT 0,
    discount_amount DECIMAL(15, 2) DEFAULT 0,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    final_amount DECIMAL(15, 2) DEFAULT 0,
    notes TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sales_orders IS '銷售訂單主檔';
COMMENT ON COLUMN sales_orders.order_number IS '訂單編號';
COMMENT ON COLUMN sales_orders.status IS '訂單狀態（pending-待處理, confirmed-已確認, manufacturing-生產中, shipped-已出貨, delivered-已送達, cancelled-已取消）';
COMMENT ON COLUMN sales_orders.payment_status IS '付款狀態（unpaid-未付款, partial-部分付款, paid-已付款）';

-- ==================== 訂單明細表 ====================
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES sales_orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(15, 2) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0,
    line_total DECIMAL(15, 2) NOT NULL,
    production_status VARCHAR(50) DEFAULT 'pending',
    scheduled_date DATE,
    completed_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE order_items IS '訂單明細表';
COMMENT ON COLUMN order_items.production_status IS '生產狀態（pending-待生產, scheduled-已排程, in_progress-生產中, completed-已完成, on_hold-暫停）';

-- ==================== 生產工單表 ====================
CREATE TABLE IF NOT EXISTS production_orders (
    id SERIAL PRIMARY KEY,
    production_number VARCHAR(50) UNIQUE NOT NULL,
    order_item_id INTEGER REFERENCES order_items(id),
    product_id INTEGER REFERENCES products(id),
    planned_quantity INTEGER NOT NULL,
    actual_quantity INTEGER DEFAULT 0,
    scrap_quantity INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'planned',
    priority VARCHAR(50) DEFAULT 'normal',
    start_date DATE,
    planned_end_date DATE,
    actual_end_date DATE,
    assigned_to VARCHAR(100),
    machine_id VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE production_orders IS '生產工單表';
COMMENT ON COLUMN production_orders.status IS '工單狀態（planned-已計劃, released-已發放, in_progress-生產中, completed-已完成, cancelled-已取消）';
COMMENT ON COLUMN production_orders.priority IS '優先級（urgent-緊急, high-高, normal-正常, low-低）';

-- ==================== 庫存異動表 ====================
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    transaction_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    reference_number VARCHAR(100),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_by VARCHAR(100)
);

COMMENT ON TABLE inventory_transactions IS '庫存異動記錄表';
COMMENT ON COLUMN inventory_transactions.transaction_type IS '異動類型（purchase-採購入庫, production-生產入庫, sales-銷售出庫, adjustment-調整, scrap-報廢）';

-- ==================== 出貨記錄表 ====================
CREATE TABLE IF NOT EXISTS shipments (
    id SERIAL PRIMARY KEY,
    shipment_number VARCHAR(50) UNIQUE NOT NULL,
    order_id INTEGER REFERENCES sales_orders(id),
    shipment_date DATE NOT NULL,
    delivery_method VARCHAR(100),
    tracking_number VARCHAR(100),
    carrier VARCHAR(100),
    status VARCHAR(50) DEFAULT 'preparing',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE shipments IS '出貨記錄表';
COMMENT ON COLUMN shipments.status IS '出貨狀態（preparing-準備中, shipped-已發出, in_transit-運送中, delivered-已送達, returned-已退回）';

-- ==================== 建立索引 ====================
CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_customers_name ON customers(customer_name);
CREATE INDEX idx_products_code ON products(product_code);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_sales_orders_number ON sales_orders(order_number);
CREATE INDEX idx_sales_orders_customer ON sales_orders(customer_id);
CREATE INDEX idx_sales_orders_date ON sales_orders(order_date);
CREATE INDEX idx_sales_orders_status ON sales_orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_production_orders_number ON production_orders(production_number);
CREATE INDEX idx_production_orders_status ON production_orders(status);
CREATE INDEX idx_inventory_product ON inventory_transactions(product_id);
CREATE INDEX idx_inventory_date ON inventory_transactions(transaction_date);
CREATE INDEX idx_shipments_order ON shipments(order_id);

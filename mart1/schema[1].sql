

CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- Added NOT NULL
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE,
    address TEXT

);


-- Categories
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);



CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,              -- product name required
    barcode VARCHAR(50) UNIQUE,              -- must be unique
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),  -- price can’t be negative
    stock_quantity INT NOT NULL DEFAULT 0,   -- default stock is 0
    category_id INT NOT NULL REFERENCES categories(category_id),
    low_stock_threshold INT DEFAULT 10,      -- default threshold for stock alert
    supplier_id INT NOT NULL REFERENCES suppliers(supplier_id)
);



-- Customers
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE
);

-- Employees
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN','CASHIER','MANAGER')),
    username VARCHAR(50) UNIQUE NOT NULL, 
    password TEXT NOT NULL
);

-- Sales
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    sale_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0  CHECK (total_amount >= 0), -- Added NOT NULL and DEFAULT
    payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('CASH','CARD','UPI','WALLET')),
    customer_id INT REFERENCES customers(customer_id) ON DELETE SET NULL,
    employee_id INT REFERENCES employees(employee_id) ON DELETE SET NULL

);

-- Sale Items
CREATE TABLE sale_items (
    sale_item_id SERIAL PRIMARY KEY,
    sale_id INT NOT NULL REFERENCES sales(sale_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    subtotal DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);


-- Purchase Orders
CREATE TABLE purchase_orders (
    order_id SERIAL PRIMARY KEY,
    supplier_id INT NOT NULL REFERENCES suppliers(supplier_id),
    order_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RECEIVED', 'CANCELLED'))

);

-- Purchase Order Items
CREATE TABLE purchase_order_items (
    order_item_id SERIAL PRIMARY KEY,
order_id INT NOT NULL REFERENCES purchase_orders(order_id) ON DELETE CASCADE,
product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    message TEXT NOT NULL,
    status VARCHAR(10) DEFAULT 'unread', -- unread / read
    notification_type VARCHAR(20) DEFAULT 'low_stock',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- =========================================
-- Audit Logs Table (for tracking all activities)
-- =========================================
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(50),
    role VARCHAR(20),
    action VARCHAR(10),
    table_name VARCHAR(50),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'SUCCESS',
    error_message TEXT
);

-- Add these to your schema if not present:

-- 1. Customer loyalty points system
ALTER TABLE customers ADD COLUMN loyalty_points INT DEFAULT 0;
ALTER TABLE customers ADD COLUMN total_spent DECIMAL(10,2) DEFAULT 0;

-- 2. Product cost price for profit calculation
ALTER TABLE products ADD COLUMN cost_price DECIMAL(10,2);

-- 3. Supplier performance tracking
ALTER TABLE suppliers ADD COLUMN reliability_score INT DEFAULT 100;
ALTER TABLE suppliers ADD COLUMN last_delivery_date DATE;

-- 4. Employee performance metrics
ALTER TABLE employees ADD COLUMN total_sales INT DEFAULT 0;
ALTER TABLE employees ADD COLUMN total_revenue DECIMAL(10,2) DEFAULT 0;



-- Add missing columns to customers table
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS address TEXT,
-- Ensure products have a threshold column
ALTER TABLE products ADD COLUMN IF NOT EXISTS low_stock_threshold INT DEFAULT 10;

-- =========================================
-- 1. Notifications Table
-- =========================================
CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    message TEXT NOT NULL,
    status VARCHAR(10) DEFAULT 'unread', -- unread / read
    notification_type VARCHAR(20) DEFAULT 'low_stock',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- =========================================
-- 2. Trigger Function: Reduce Stock + Alert
-- =========================================
CREATE OR REPLACE FUNCTION reduce_stock_and_alert()
RETURNS TRIGGER AS $$
DECLARE
    current_stock INT;
    product_name TEXT;
    supplier_name INT;
    threshold INT;
BEGIN
    -- Reduce stock and fetch current values
    UPDATE products
    SET stock_quantity = stock_quantity - NEW.quantity
    WHERE product_id = NEW.product_id
    RETURNING stock_quantity, name, supplier_id, low_stock_threshold
    INTO current_stock, product_name, supplier_name, threshold;

    -- Prevent negative stock
    IF current_stock < 0 THEN
        RAISE EXCEPTION 'Not enough stock for product: %', product_name;
    END IF;

    -- Low stock notification
    IF current_stock < threshold THEN
        INSERT INTO notifications (product_id, message, notification_type)
        VALUES (
            NEW.product_id,
            CONCAT('Stock running low for "', product_name, '" (Remaining: ', current_stock, ')'),
            'low_stock'
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =========================================
-- 3. Trigger on sale_items
-- =========================================
DROP TRIGGER IF EXISTS trg_reduce_stock_and_alert ON sale_items;
CREATE TRIGGER trg_reduce_stock_and_alert
AFTER INSERT ON sale_items
FOR EACH ROW
EXECUTE FUNCTION reduce_stock_and_alert();

-- =========================================
-- 4. Views / Reports
-- =========================================

-- Daily Sales Report (with transaction count & average)
CREATE OR REPLACE VIEW daily_sales_report AS
SELECT DATE(s.sale_time) AS date,
       SUM(s.total_amount) AS total_sales,
       COUNT(s.sale_id) AS transactions,
       ROUND(AVG(s.total_amount), 2) AS avg_sale
FROM sales s
GROUP BY DATE(s.sale_time)
ORDER BY date DESC;

-- Best Selling Products (with revenue & category)
CREATE OR REPLACE VIEW best_selling_products AS
SELECT p.product_id,
       p.name AS product,
       c.name AS category,
       SUM(si.quantity) AS total_sold,
       SUM(si.quantity * si.unit_price) AS total_revenue
FROM sale_items si
JOIN products p ON si.product_id = p.product_id
LEFT JOIN categories c ON p.category_id = c.category_id
GROUP BY p.product_id, p.name, c.name
ORDER BY total_sold DESC;

-- Low Stock Products (with supplier info)
CREATE OR REPLACE VIEW low_stock_products AS
SELECT p.product_id,
       p.name AS product,
       p.stock_quantity,
       s.name AS supplier_name
FROM products p
LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
WHERE p.stock_quantity < COALESCE(p.low_stock_threshold, 10)
ORDER BY p.stock_quantity ASC;

-- =========================================
-- 5. Performance Indexes (Added Jan 2026)
-- =========================================

-- Sales table indexes (most queried for analytics)
CREATE INDEX IF NOT EXISTS idx_sales_sale_time ON sales(sale_time DESC);
CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_employee_id ON sales(employee_id);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(DATE(sale_time));

-- Products table indexes (for product listings and lookups)
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_products_stock ON products(stock_quantity);
CREATE INDEX IF NOT EXISTS idx_products_low_stock ON products(stock_quantity, low_stock_threshold);

-- Sale items for analytics queries
CREATE INDEX IF NOT EXISTS idx_sale_items_product_id ON sale_items(product_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id);

-- Customers table indexes
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- Employees table indexes
CREATE INDEX IF NOT EXISTS idx_employees_username ON employees(username);
CREATE INDEX IF NOT EXISTS idx_employees_role ON employees(role);

-- Audit logs indexes (if audit table exists)
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
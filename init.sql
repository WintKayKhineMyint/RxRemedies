-- ===========================
--   Rx Remedies: init.sql
-- ===========================
-- 1) Create 'categories' table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- 2) Create 'medicines' table with QUANTITY
CREATE TABLE IF NOT EXISTS medicines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    category_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- 3) Create 'customers' table
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    address VARCHAR(200)
);

-- 4) Create 'orders' table (links customer <-> medicine)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    medicine_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

-- 5) Create a view: 'medicines_with_categories'
CREATE OR REPLACE VIEW medicines_with_categories AS
SELECT m.id AS medicine_id,
       m.name AS medicine_name,
       m.price,
       c.name AS category_name,
       m.quantity,
       m.created_at
FROM medicines m
JOIN categories c ON m.category_id = c.id;

-- 6) Create a view: 'orders_details'
CREATE OR REPLACE VIEW orders_details AS
SELECT o.id AS order_id,
       cust.full_name AS customer_name,
       med.name AS medicine_name,
       o.quantity,
       med.price,
       (o.quantity * med.price) AS total_cost,
       o.created_at AS order_time
FROM orders o
JOIN customers cust ON o.customer_id = cust.id
JOIN medicines med ON o.medicine_id = med.id;

-- 7) Trigger function for 'medicines' to set created_at
CREATE OR REPLACE FUNCTION set_medicine_created_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_insert_medicine_timestamp ON medicines;
CREATE TRIGGER trigger_insert_medicine_timestamp
BEFORE INSERT ON medicines
FOR EACH ROW
EXECUTE PROCEDURE set_medicine_created_at();

-- 8) Trigger function for 'orders' to set created_at
CREATE OR REPLACE FUNCTION set_order_created_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_insert_order_timestamp ON orders;
CREATE TRIGGER trigger_insert_order_timestamp
BEFORE INSERT ON orders
FOR EACH ROW
EXECUTE PROCEDURE set_order_created_at();

-- 9) Optionally insert some categories
INSERT INTO categories(name) VALUES
('Pain Relief'),
('Antibiotics'),
('Vitamins')
ON CONFLICT DO NOTHING;

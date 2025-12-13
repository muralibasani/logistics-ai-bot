-- 1. Customers
CREATE TABLE LG_Customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(15)
);

-- 2. Customer_Account_Info
CREATE TABLE LG_Customer_Account_Info (
    account_id SERIAL PRIMARY KEY,
    customer_id INT,
    phone_number VARCHAR(15),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(20),
    country VARCHAR(100),
    address_type VARCHAR(50),
    is_default BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (customer_id) REFERENCES LG_Customers(customer_id)
);

-- 3. Orders
CREATE TABLE LG_Orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    order_status VARCHAR(50),
    total_amount DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES LG_Customers(customer_id)
);

-- 4. Order_Items
CREATE TABLE LG_Order_Items (
    item_id SERIAL PRIMARY KEY,
    order_id INT,
    product_name VARCHAR(150),
    quantity INT,
    price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES LG_Orders(order_id)
);

-- 5. Order_Tracking
CREATE TABLE LG_Order_Tracking (
    tracking_id SERIAL PRIMARY KEY,
    order_id INT,
    status VARCHAR(100),
    location VARCHAR(150),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES LG_Orders(order_id)
);

-- 6. Order_Cancellation
CREATE TABLE LG_Order_Cancellation (
    cancel_id SERIAL PRIMARY KEY,
    order_id INT,
    cancel_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(255),
    cancelled_by VARCHAR(50),
    FOREIGN KEY (order_id) REFERENCES LG_Orders(order_id)
);

-- 7. Refunds
CREATE TABLE LG_Refunds (
    refund_id SERIAL PRIMARY KEY,
    order_id INT,
    refund_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    refund_amount DECIMAL(10,2),
    refund_status VARCHAR(50),
    FOREIGN KEY (order_id) REFERENCES LG_Orders(order_id)
);

-- 8. Delivered_Orders (Optional)
CREATE TABLE LG_Delivered_Orders (
    delivery_id SERIAL PRIMARY KEY,
    order_id INT,
    delivered_date TIMESTAMP,
    delivery_person VARCHAR(100),
    comments VARCHAR(255),
    FOREIGN KEY (order_id) REFERENCES LG_Orders(order_id)
);

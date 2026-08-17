INSERT INTO warehouses (code, name, capacity, used_capacity) VALUES
('WH-GUW', 'Guwahati Fulfillment Center', 10000, 0),
('WH-KOL', 'Kolkata Fulfillment Center', 15000, 0)
ON CONFLICT (code) DO NOTHING;

INSERT INTO products (sku, name, price) VALUES
('SKU-1001', 'Wireless Headphones', 2499.00),
('SKU-1002', 'Mechanical Keyboard', 4999.00),
('SKU-1003', 'USB-C Charger', 1499.00)
ON CONFLICT (sku) DO NOTHING;

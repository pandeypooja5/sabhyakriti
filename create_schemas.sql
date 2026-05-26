-- Create schemas for each microservice
CREATE SCHEMA IF NOT EXISTS product;
CREATE SCHEMA IF NOT EXISTS cart;
CREATE SCHEMA IF NOT EXISTS orders;
CREATE SCHEMA IF NOT EXISTS payment;
CREATE SCHEMA IF NOT EXISTS notification;

-- Verify schemas were created
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('product', 'cart', 'orders', 'payment', 'notification')
ORDER BY schema_name;

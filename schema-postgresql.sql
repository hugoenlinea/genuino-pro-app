-- schema-postgresql.sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    fullname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Vendedor',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    nit_ci TEXT NOT NULL UNIQUE,
    address TEXT,
    contact_person TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    setting_key VARCHAR(255) PRIMARY KEY,
    setting_value TEXT
);

CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    quote_number TEXT NOT NULL UNIQUE,
    customer_id INT NOT NULL REFERENCES customers(id),
    user_id INT NOT NULL REFERENCES users(id),
    total_amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'Borrador',
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    quote_id INT NOT NULL UNIQUE REFERENCES quotes(id),
    order_status TEXT NOT NULL DEFAULT 'Pendiente',
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS catalog_types (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS catalog (
    id SERIAL PRIMARY KEY,
    type_id INT NOT NULL REFERENCES catalog_types(id),
    code TEXT NOT NULL,
    description TEXT NOT NULL,
    unit_price REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(type_id, code)
);

CREATE TABLE IF NOT EXISTS quote_items (
    id SERIAL PRIMARY KEY,
    quote_id INT NOT NULL REFERENCES quotes(id),
    type_id INT NOT NULL REFERENCES catalog_types(id),
    code TEXT,
    description TEXT NOT NULL,
    quantity INT NOT NULL,
    unit_price REAL NOT NULL,
    subtotal REAL NOT NULL
);
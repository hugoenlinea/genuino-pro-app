-- schema.sql
PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Vendedor', -- 'Vendedor' o 'Jefe de Ventas'
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    nit_ci TEXT NOT NULL UNIQUE, -- ¡CAMBIO AÑADIDO!
    address TEXT,
    contact_person TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE app_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL UNIQUE,
    order_status TEXT NOT NULL DEFAULT 'Pendiente', -- Ej: Pendiente, En Proceso, Enviado, Completado
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes (id)
);

CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_number TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'Borrador', -- Borrador, Pendiente de Aprobacion, Aprobada, Rechazada
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE catalog_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    description TEXT NOT NULL,
    unit_price REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES catalog_types (id),
    UNIQUE(type_id, code)
);

CREATE TABLE quote_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    code TEXT,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (quote_id) REFERENCES quotes (id),
    FOREIGN KEY (type_id) REFERENCES catalog_types (id)
);
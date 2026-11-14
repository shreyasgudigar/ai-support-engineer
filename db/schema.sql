CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,

    customer_id INTEGER NOT NULL
        REFERENCES customers(id)
        ON DELETE CASCADE,

    product_name VARCHAR(255) NOT NULL,

    status VARCHAR(50) NOT NULL,

    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    expected_delivery_date DATE
);


CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,

    customer_id INTEGER
        REFERENCES customers(id)
        ON DELETE SET NULL,

    message TEXT NOT NULL,

    category VARCHAR(100),

    predicted_category VARCHAR(100),

    confidence DOUBLE PRECISION,

    status VARCHAR(50) DEFAULT 'open',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,

    title VARCHAR(255) NOT NULL,

    content TEXT NOT NULL,

    embedding VECTOR(384),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
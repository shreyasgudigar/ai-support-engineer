INSERT INTO customers (name, email)
VALUES
    ('Rahul Kumar', 'rahul@example.com'),
    ('Ananya Rao', 'ananya@example.com');


INSERT INTO orders (
    customer_id,
    product_name,
    status,
    expected_delivery_date
)
VALUES
    (
        1,
        'Laptop',
        'shipped',
        CURRENT_DATE + 3
    ),
    (
        2,
        'Wireless Headphones',
        'delivered',
        CURRENT_DATE
    );


INSERT INTO support_tickets (
    customer_id,
    message,
    category
)
VALUES
    (
        1,
        'Where is my laptop order?',
        'shipping'
    ),
    (
        2,
        'I want to return my headphones',
        'refund'
    ),
    (
        1,
        'My payment failed',
        'payment'
    );


INSERT INTO knowledge_documents (
    title,
    content
)
VALUES
    (
        'Return Policy',
        'Eligible products can be returned within 30 days of delivery.'
    ),
    (
        'Shipping Policy',
        'Orders normally arrive within 3 to 7 business days after shipment.'
    );
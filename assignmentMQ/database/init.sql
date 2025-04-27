USE tododb;

CREATE TABLE todos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text VARCHAR(255) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add some initial todo items
INSERT INTO todos (text, completed) VALUES
    ('Learn Docker', true),
    ('Understand 3-layer architecture', false),
    ('Implement RabbitMQ messaging', false),
    ('Complete the assignment', false);

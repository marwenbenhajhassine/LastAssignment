-- Set up the database for replication
USE tododb;

-- Create the 'todos' table
CREATE TABLE todos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text VARCHAR(255) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some initial todo items
INSERT INTO todos (text, completed) VALUES
    ('Learn Docker', true),
    ('Understand 3-layer architecture', false),
    ('Implement RabbitMQ messaging', false),
    ('Complete the assignment', false);

-- Create replication user for primary (master) and replica servers
CREATE USER 'repl_user'@'%' IDENTIFIED BY 'repl_password';

-- Grant the replication user REPLICATION SLAVE privileges
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'%';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;


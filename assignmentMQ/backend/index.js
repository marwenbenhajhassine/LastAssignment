const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const mysql = require('mysql2/promise');
const amqp = require('amqplib');

const app = express();
const PORT = 3030;
const port = 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Get the backend instance ID from environment variables
const backendId = process.env.BACKEND_ID || 'unknown-backend';

// Database configuration
const dbConfig = {
  host: process.env.MYSQL_HOST || 'todo-db',
  user: process.env.MYSQL_USER || 'todo_user',
  password: process.env.MYSQL_PASSWORD || 'todo_password',
  database: process.env.MYSQL_DATABASE || 'tododb'
};

// RabbitMQ configuration
const rabbitConfig = {
  host: process.env.RABBITMQ_HOST || 'rabbitmq',
  user: process.env.RABBITMQ_USER || 'guest',
  password: process.env.RABBITMQ_PASS || 'guest'
};

// Connect to database function
const connectToDatabase = async () => {
  try {
    const connection = await mysql.createConnection(dbConfig);
    console.log('Connected to MySQL database');
    return connection;
  } catch (error) {
    console.error('Database connection error:', error);
    // Retry connection after delay
    console.log('Retrying database connection in 5 seconds...');
    setTimeout(connectToDatabase, 5000);
    return null;
  }
};

// Global database connection
let db;

// Connect to RabbitMQ
let channel;
const connectToRabbitMQ = async () => {
  try {
    const conn = await amqp.connect(`amqp://${rabbitConfig.user}:${rabbitConfig.password}@${rabbitConfig.host}`);
    channel = await conn.createChannel();
    
    // Declare queue for todo events
    await channel.assertQueue('todo_events', { durable: true });
    
    console.log('Connected to RabbitMQ');
    return channel;
  } catch (error) {
    console.error('RabbitMQ connection error:', error);
    console.log('Retrying RabbitMQ connection in 5 seconds...');
    setTimeout(connectToRabbitMQ, 5000);
    return null;
  }
};

// Initialize connections
(async () => {
  db = await connectToDatabase();
  channel = await connectToRabbitMQ();
})();

// Publish event to RabbitMQ
const publishEvent = async (eventType, data) => {
  if (!channel) {
    channel = await connectToRabbitMQ();
    if (!channel) return;
  }
  
  try {
    channel.sendToQueue(
      'todo_events',
      Buffer.from(JSON.stringify({ event: eventType, data })),
      { persistent: true }
    );
    console.log(`Published ${eventType} event`);
  } catch (error) {
    console.error('Error publishing event:', error);
  }
};

// Routes
app.get('/api/todos', async (req, res) => {
  try {
    if (!db) {
      db = await connectToDatabase();
      if (!db) return res.status(500).json({ error: 'Database unavailable' });
    }
    
    const [rows] = await db.query('SELECT * FROM todos ORDER BY created_at DESC');
    res.json(rows);
  } catch (error) {
    console.error('Error fetching todos:', error);
    res.status(500).json({ error: 'Failed to fetch todos' });
  }
});

app.post('/api/todos', async (req, res) => {
  try {
    const { text } = req.body;
    if (!text) return res.status(400).json({ error: 'Text is required' });
    
    if (!db) {
      db = await connectToDatabase();
      if (!db) return res.status(500).json({ error: 'Database unavailable' });
    }
    
    const [result] = await db.query('INSERT INTO todos (text) VALUES (?)', [text]);
    const [newTodo] = await db.query('SELECT * FROM todos WHERE id = ?', [result.insertId]);
    
    // Publish todo created event
    await publishEvent('todo_created', newTodo[0]);
    
    res.status(201).json(newTodo[0]);
  } catch (error) {
    console.error('Error creating todo:', error);
    res.status(500).json({ error: 'Failed to create todo' });
  }
});

app.put('/api/todos/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { completed } = req.body;
    
    if (!db) {
      db = await connectToDatabase();
      if (!db) return res.status(500).json({ error: 'Database unavailable' });
    }
    
    await db.query('UPDATE todos SET completed = ? WHERE id = ?', [completed, id]);
    const [updated] = await db.query('SELECT * FROM todos WHERE id = ?', [id]);
    
    if (updated.length === 0) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    
    // Publish todo updated event
    await publishEvent('todo_updated', updated[0]);
    
    res.json(updated[0]);
  } catch (error) {
    console.error('Error updating todo:', error);
    res.status(500).json({ error: 'Failed to update todo' });
  }
});

app.delete('/api/todos/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    if (!db) {
      db = await connectToDatabase();
      if (!db) return res.status(500).json({ error: 'Database unavailable' });
    }
    
    // Get todo before deletion
    const [todo] = await db.query('SELECT * FROM todos WHERE id = ?', [id]);
    if (todo.length === 0) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    
    await db.query('DELETE FROM todos WHERE id = ?', [id]);
    
    // Publish todo deleted event
    await publishEvent('todo_deleted', todo[0]);
    
    res.json(todo[0]);
  } catch (error) {
    console.error('Error deleting todo:', error);
    res.status(500).json({ error: 'Failed to delete todo' });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/', (req, res) => {
  res.send(`Hello from ${backendId}`);
});

// Start server
app.listen(PORT, () => {
  console.log(`Backend server running on port ${PORT}`);
});

app.listen(port, () => {
  console.log(`Backend ${backendId} listening on port ${port}`);
});
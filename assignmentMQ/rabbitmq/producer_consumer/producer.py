#!/usr/bin/env python
import pika
import json
import time
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RabbitMQ connection parameters
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')
QUEUE_NAME = 'todo_tasks'

def create_connection():
    """Create a connection to RabbitMQ with retry logic"""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    
    MAX_RETRIES = 12
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            connection = pika.BlockingConnection(parameters)
            logger.info("Successfully connected to RabbitMQ")
            return connection
        except pika.exceptions.AMQPConnectionError:
            retry_count += 1
            retry_delay = min(10, 2 ** retry_count)  # Exponential backoff with max delay of 10s
            logger.info(f"Connection attempt {retry_count} failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    raise Exception("Failed to connect to RabbitMQ after multiple attempts")

def main():
    """Main producer function"""
    connection = create_connection()
    channel = connection.channel()
    
    # Declare a queue for task messages
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    try:
        message_count = 0
        while True:
            message_count += 1
            message = {
                'task_id': message_count,
                'description': f"Task {message_count}",
                'created_at': datetime.now().isoformat()
            }
            
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Makes message persistent
                )
            )
            
            logger.info(f"Sent task {message_count}")
            time.sleep(5)  # Send a task every 5 seconds

    except KeyboardInterrupt:
        logger.info("Producer interrupted")
        connection.close()

if __name__ == '__main__':
    main()

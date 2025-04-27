#!/usr/bin/env python
import pika
import json
import time
import os
import logging

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

def process_task(ch, method, properties, body):
    """Process a task from the queue"""
    try:
        task = json.loads(body)
        logger.info(f"Processing task: {task}")
        
        # Simulate task processing time
        time.sleep(2)
        
        logger.info(f"Task {task.get('task_id')} completed")
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    except Exception as e:
        logger.error(f"Error processing task: {e}")
        # Nack the message to requeue it
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    """Main consumer function"""
    connection = create_connection()
    channel = connection.channel()
    
    # Declare the queue from which we'll consume
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Set prefetch count to 1 to ensure fair dispatch
    channel.basic_qos(prefetch_count=1)
    
    # Register the callback
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_task)
    
    logger.info('Consumer started. Waiting for tasks...')
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Consumer interrupted")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()

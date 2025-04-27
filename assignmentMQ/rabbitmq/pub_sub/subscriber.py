#!/usr/bin/env python
import pika
import json
import time
import os
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RabbitMQ connection parameters
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')
EXCHANGE_NAME = 'todo_events'
SUBSCRIBER_NAME = os.environ.get('SUBSCRIBER_NAME', f'subscriber-{uuid.uuid4().hex[:8]}')

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
            retry_delay = min(10, 2 ** retry_count)
            logger.info(f"Connection attempt {retry_count} failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    raise Exception("Failed to connect to RabbitMQ after multiple attempts")

def process_event(ch, method, properties, body):
    """Process an event from the exchange"""
    try:
        event = json.loads(body)
        logger.info(f"[{SUBSCRIBER_NAME}] Received {event.get('event_type')} event: {event}")
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        # Nack the message
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    """Main subscriber function"""
    connection = create_connection()
    channel = connection.channel()
    
    # Declare the fanout exchange
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')
    
    # Create an exclusive queue with a generated name
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    
    # Bind the queue to the exchange
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)
    
    # Register the callback
    channel.basic_consume(queue=queue_name, on_message_callback=process_event)
    
    logger.info(f"Subscriber {SUBSCRIBER_NAME} started. Waiting for events...")
    
    try:
        
      channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Subscriber interrupted. Closing connection.")
        connection.close()

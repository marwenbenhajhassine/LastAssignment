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
EXCHANGE_NAME = 'todo_events'

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

def main():
    """Main publisher function"""
    connection = create_connection()
    channel = connection.channel()
    
    # Declare a fanout exchange
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')
    
    try:
        message_count = 0
        event_types = ['todo_created', 'todo_updated', 'todo_deleted']
        
        while True:
            message_count += 1
            event_type = event_types[message_count % len(event_types)]
            
            message = {
                'event_type': event_type,
                'todo_id': message_count,
                'data': {
                    'text': f"Task {message_count}",
                    'completed': message_count % 2 == 0,
                },
                'timestamp': datetime.now().isoformat()
            }
            
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key='',  # fanout exchange ignores routing key
                body=json.dumps(message)
            )
            
            logger.info(f"Published {event_type} event for todo {message_count}")
            time.sleep(7)  # Publish event every 7 seconds

    except KeyboardInterrupt:
        logger.info("Publisher interrupted")
        connection.close()

if __name__ == '__main__':
    main()

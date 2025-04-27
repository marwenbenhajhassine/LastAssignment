#!/usr/bin/env python
import pika
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')

def process_request(request):
    logger.info(f"Processing request: {request}")
    # Dummy response logic
    return {"status": "success", "info": f"Details for movie {request.get('movie_id')}"}

def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='rpc_queue')

    def on_request(ch, method, props, body):
        request = json.loads(body)
        response = process_request(request)
        response_body = json.dumps(response)

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=response_body)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

    logger.info("Reply service is waiting for requests...")
    channel.start_consuming()

if __name__ == '__main__':
    main()

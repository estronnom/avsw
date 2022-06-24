import json
import os
import subprocess

from utils.mqinterface import get_pika_connection, publish_message

RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
SPIDER_QUEUE = os.environ['SPIDER_QUEUE']
PARSER_QUEUE = os.environ['PARSER_QUEUE']
ERRORS_QUEUE = os.environ['ERRORS_QUEUE']

connection = get_pika_connection(RABBITMQ_HOST)
channel = connection.channel()
channel.queue_declare(SPIDER_QUEUE, durable=True)
channel.queue_declare(PARSER_QUEUE, durable=True)
channel.queue_declare(ERRORS_QUEUE, durable=True)


def is_file_text(path):
    file_info = subprocess.Popen(['file', path], stdout=subprocess.PIPE)
    file_info = file_info.communicate()[0].decode()
    file_info = file_info.split(':')[1].split(';')[0]
    return 'text' in file_info


def callback(ch, method, properties, body):
    print('Sender got a callback!')
    body_decoded = json.loads(body.decode())
    path = body_decoded["path"]
    queue = PARSER_QUEUE if is_file_text(path) else ERRORS_QUEUE
    if publish_message(channel, queue, body):
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print('Message acknowledged')


def main():
    channel.basic_consume(
        SPIDER_QUEUE,
        callback
    )
    print('Sender ready to consume!')
    channel.start_consuming()


if __name__ == '__main__':
    main()

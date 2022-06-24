import os
import mimetypes

from utils.mqinterface import get_pika_connection

RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
SPIDER_QUEUE = os.environ['SPIDER_QUEUE']
PARSER_QUEUE = os.environ['PARSER_QUEUE']
ERRORS_QUEUE = os.environ['ERRORS_QUEUE']

connection = get_pika_connection(RABBITMQ_HOST)
channel = connection.channel()
channel.queue_declare(SPIDER_QUEUE)
channel.queue_declare(PARSER_QUEUE)
channel.queue_declare(ERRORS_QUEUE)


def callback(ch, method, properties, body):
    print('Sender got a callback!')


def main():
    channel.basic_consume(
        SPIDER_QUEUE,
        callback,
        auto_ack=True
    )
    print('Sender ready to consume!')
    channel.start_consuming()


if __name__ == '__main__':
    main()

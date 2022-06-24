import os
import re
import json
from collections import defaultdict

from utils.dbinterface import Database
from utils.mqinterface import get_pika_connection, publish_message

MYSQL_HOST = os.environ['MYSQL_HOST']
MYSQL_USER = os.environ['MYSQL_USER']
MYSQL_DATABASE = os.environ['MYSQL_DATABASE']
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
PARSER_QUEUE = os.environ['PARSER_QUEUE']
READER_QUEUE = os.environ['READER_QUEUE']

db = Database(host=MYSQL_HOST,
              user=MYSQL_USER,
              password=MYSQL_PASSWORD,
              database=MYSQL_DATABASE)

connection = get_pika_connection(RABBITMQ_HOST)
channel = connection.channel()
channel.queue_declare(PARSER_QUEUE, durable=True)
channel.queue_declare(READER_QUEUE, durable=True)


def insert_words(words_dict):
    pass


def parse_file(path):
    words_dict = defaultdict(int)
    try:
        with open(path, 'r') as fh:
            for line in fh:
                line = line.strip().replace('\xa0', '')
                line = re.findall(r'\s[a-zA-Zа-яА-Я][a-zA-Zа-яА-Я]+\s', line)
                for word in line:
                    word = word.lower()
                    words_dict[word] += 1
    except OSError as exc:
        print(f'Error while parsing file {path}')
        print(exc)
    else:
        print(f'Successefully parsed file {path}')
    finally:
        return dict(words_dict)


def callback(ch, method, properties, body):
    print('Parser got a callback!')
    body_decoded = json.loads(body.decode())
    path = body_decoded["path"]
    words_dict = parse_file(path)
    print(words_dict)
    if words_dict and insert_words(words_dict):
        if publish_message(channel):
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print(words_dict)
            print('Parser acknowledged message')


def main():
    channel.basic_consume(
        PARSER_QUEUE,
        callback
    )
    print('Parser ready to consume!')
    channel.start_consuming()


if __name__ == '__main__':
    main()

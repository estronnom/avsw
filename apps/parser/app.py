import os
import re
import json
import time
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
db.execute(
    "CREATE TABLE IF NOT EXISTS words ("
    "word_id INT PRIMARY KEY AUTO_INCREMENT, "
    "word VARCHAR(255) UNIQUE NOT NULL, "
    "counter INT"
    ");"
)
db.execute(
    "CREATE TABLE IF NOT EXISTS files ("
    "file_id INT PRIMARY KEY AUTO_INCREMENT, "
    "file_name VARCHAR(255) UNIQUE NOT NULL"
    ");"
)
db.execute(
    "CREATE TABLE IF NOT EXISTS word_file ("
    "word_id INT NOT NULL, "
    "file_id INT NOT NULL,"
    "FOREIGN KEY (word_id) REFERENCES words(word_id) "
    "ON DELETE CASCADE ,"
    "FOREIGN KEY (file_id) REFERENCES files(file_id),"
    "UNIQUE (word_id, file_id)"
    ");"
)

connection = get_pika_connection(RABBITMQ_HOST)
channel = connection.channel()
channel.queue_declare(PARSER_QUEUE, durable=True)
channel.queue_declare(READER_QUEUE, durable=True)


def insert_words(words_dict, file_name):
    x0 = time.time()
    db.execute(
        "INSERT IGNORE INTO files(file_name)"
        "VALUES (%s)",
        (file_name,)
    )
    file_id = db.execute(
        "SELECT file_id FROM files WHERE "
        "file_name = %s",
        (file_name,))[0][0]

    for word, counter in words_dict.items():
        db.execute(
            "INSERT INTO words(word, counter) "
            "VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE counter=counter+%s",
            (word, counter, counter)
        )
        db.execute(
            "INSERT IGNORE INTO word_file(word_id, file_id) "
            "SELECT"
            "(SELECT word_id FROM words"
            " WHERE word=%s),"
            "%s",
            (word, file_id)
        )
    print(time.time() - x0)


def parse_file(path):
    words_dict = defaultdict(int)
    try:
        with open(path, 'r') as fh:
            for line in fh:
                line = line.strip().replace('\xa0', '')
                line = re.findall(
                    r'[a-zA-Zа-яА-Я][a-zA-Zа-яА-Я]+',
                    line
                )
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
    file_name = os.path.split(path)[-1]
    if words_dict:
        insert_words(words_dict, file_name)
        if publish_message(channel, READER_QUEUE, body):
            channel.basic_ack(delivery_tag=method.delivery_tag)
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

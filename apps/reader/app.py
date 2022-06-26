import os
import json
import time

from telebot import TeleBot

from utils.dbinterface import Database
from utils.mqinterface import get_pika_connection

WORD_COUNTER = os.environ['WORD_COUNTER']
MYSQL_HOST = os.environ['MYSQL_HOST']
MYSQL_USER = os.environ['MYSQL_USER']
MYSQL_DATABASE = os.environ['MYSQL_DATABASE']
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
READER_QUEUE = os.environ['READER_QUEUE']

FILE_FOLDER = './processed_files/'

db = Database(host=MYSQL_HOST,
              user=MYSQL_USER,
              password=MYSQL_PASSWORD,
              database=MYSQL_DATABASE)

connection = get_pika_connection(RABBITMQ_HOST)
channel = connection.channel()
channel.queue_declare(READER_QUEUE, durable=True)

TG_API_KEY = os.environ['TG_API_KEY']
bot = TeleBot(TG_API_KEY)


def clear_db(token):
    db.execute(
        "DELETE FROM words "
        "WHERE counter >= %s AND "
        "token = %s",
        (WORD_COUNTER, token)
    )


def generate_files(data_list):
    for word, file in data_list:
        path = FILE_FOLDER + word + '.txt'
        try:
            with open(path, 'a') as fh:
                fh.write(file + '\n')
        except OSError as exc:
            print('Generating files error')
            print(exc)
            return False
    return True


def observe_db(token):
    data_list = db.execute(
        "SELECT w.word, f.file_name "
        "FROM word_file "
        "JOIN words w ON w.word_id = word_file.word_id "
        "AND w.counter >= %s AND w.token = %s "
        "JOIN files f ON f.file_id = word_file.file_id "
        "ORDER BY 1",
        (WORD_COUNTER, token)
    )
    return data_list


def callback(ch, method, properties, body):
    x0 = time.time()
    print('Reader got a callback!')
    body_decoded = json.loads(body.decode())
    chat_id = body_decoded["chat_id"]
    path = body_decoded["path"]
    token = body_decoded["token"]
    file_name = os.path.split(path)[-1]
    data_list = observe_db(token)

    if generate_files(data_list):
        clear_db(token)
        bot.send_message(
            chat_id,
            f'Файл {file_name} успешно обработан'
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print('Reader acknowledged message')
    print(time.time() - x0)


def main():
    channel.basic_consume(
        READER_QUEUE,
        callback
    )
    print('Reader ready to consume!')
    channel.start_consuming()


if __name__ == '__main__':
    main()

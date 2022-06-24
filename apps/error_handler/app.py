import json
import os
from telebot import TeleBot

from utils.mqinterface import get_pika_connection

RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
ERRORS_QUEUE = os.environ['ERRORS_QUEUE']
connection = get_pika_connection(RABBITMQ_HOST)
channel = connection.channel()
channel.queue_declare(ERRORS_QUEUE, durable=True)

TG_API_KEY = os.environ['TG_API_KEY']
bot = TeleBot(TG_API_KEY)


def notify_user(chat_id, file):
    try:
        bot.send_message(
            chat_id,
            f'Во время обработки файла {file} произошла ошибка\n'
            'Файл не является текстовым'
        )
    except Exception as exc:
        print(f'Error while notifying user {chat_id} file {file}')
        print(exc)
        return False
    else:
        return True


def callback(ch, method, properties, body):
    print('Error handler got a callback!')
    body_decoded = json.loads(body.decode())
    file = os.path.split(body_decoded["path"])[-1]
    chat_id = body_decoded["chat_id"]
    if notify_user(chat_id, file):
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print('Error handler acknowledged message')


def main():
    channel.basic_consume(
        ERRORS_QUEUE,
        callback
    )
    print('Error handler ready to consume!')
    channel.start_consuming()


if __name__ == '__main__':
    main()

import secrets
import os
from telebot import TeleBot
import requests

from utils.mqinterface import get_pika_connection

RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
SPIDER_QUEUE = os.environ['SPIDER_QUEUE']

TG_API_KEY = os.environ['TG_API_KEY']
bot = TeleBot(TG_API_KEY)


def send_file_to_queue(path, chat_id):
    connection = get_pika_connection(RABBITMQ_HOST)
    channel = connection.channel()
    channel.queue_declare(SPIDER_QUEUE)

    payload = f'{path}:{chat_id}'.encode()
    try:
        channel.basic_publish(
            exchange='',
            routing_key=SPIDER_QUEUE,
            body=payload
        )
        print(f'Payload to {SPIDER_QUEUE} successfully sent')
    except Exception as exc:
        print(f'{payload} publish failed')
        print(exc)
    finally:
        connection.close()


def write_file(file_bytes, file_name):
    path = './raw_files/' + file_name
    try:
        with open(path, 'wb') as fh:
            fh.write(file_bytes)
    except OSError as exc:
        print(f'Write to {path} failed')
        print(exc)
        return None
    else:
        return path


def download_webpage(url):
    try:
        r = requests.get(url)
    except OSError as exc:
        print(f'Request to {url} failed')
        print(exc)
        return None

    token = secrets.token_urlsafe(16)
    path = './raw_files/' + token + '.txt'
    try:
        with open(path, 'x', encoding='utf-8') as fh:
            fh.write(r.text)
    except Exception as exc:
        print(f'Write to {path} failed')
        print(exc)
        return None
    else:
        return path


@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        'Для работы с ботом отправьте ему валидный URL или файл')


@bot.message_handler(content_types=['document'])
def document_handler(message):
    file_name = message.document.file_name
    file_obj = bot.get_file(message.document.file_id)
    file_bytes = bot.download_file(file_obj.file_path)
    path = write_file(file_bytes, file_name)
    if path:
        send_file_to_queue(path, message.chat.id)
        bot.send_message(
            message.chat.id,
            'Файл успешно загружен и направлен в обработку')
    else:
        bot.send_message(
            message.chat.id,
            'Произошла ошибка скачивания файла')


@bot.message_handler()
def url_handler(message):
    path = download_webpage(message.text)
    if path:
        send_file_to_queue(path, message.chat.id)
        bot.send_message(
            message.chat.id,
            'Файл успешно загружен и направлен в обработку')
    else:
        bot.send_message(
            message.chat.id,
            'Ошибка запроса к сайту, проверьте корректность URL')


if __name__ == '__main__':
    try:
        print('Starting polling...')
        bot.infinity_polling()
    except Exception as exc:
        print('Polling failed')
        print(exc)

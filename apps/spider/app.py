import json
import secrets
import os
from telebot import TeleBot
from bs4 import BeautifulSoup
import requests

from utils.mqinterface import get_pika_connection, publish_message

RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
SPIDER_QUEUE = os.environ['SPIDER_QUEUE']

TG_API_KEY = os.environ['TG_API_KEY']
bot = TeleBot(TG_API_KEY)


def send_file_to_queue(path, chat_id):
    connection = get_pika_connection(RABBITMQ_HOST)
    channel = connection.channel()
    channel.queue_declare(SPIDER_QUEUE, durable=True)

    body = {
        "path": path,
        "chat_id": chat_id
    }
    body = json.dumps(body).encode()
    result = publish_message(channel, SPIDER_QUEUE, body)
    connection.close()
    return result


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
        r.encoding = 'utf-8'
    except OSError as exc:
        print(f'Request to {url} failed')
        print(exc)
        return None

    soup = BeautifulSoup(r.text, 'lxml')
    page_text = soup.get_text(' ')

    token = secrets.token_urlsafe(16)
    path = './raw_files/' + token + '.txt'
    try:
        with open(path, 'x', encoding='utf-8') as fh:
            fh.write(page_text)
    except Exception as exc:
        print(f'Write to {path} failed')
        print(exc)
        return None
    else:
        return path


@bot.message_handler(commands=['start', 'help'])
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

    if path and send_file_to_queue(path, message.chat.id):
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

    if path and send_file_to_queue(path, message.chat.id):
        file_name = os.path.split(path)[-1]
        bot.send_message(
            message.chat.id,
            f'Файл {file_name} успешно загружен и направлен в обработку')
    else:
        bot.send_message(
            message.chat.id,
            'Ошибка запроса к сайту, проверьте корректность URL')


@bot.message_handler(commands=['dump'])
def dump_files(message):
    pass


if __name__ == '__main__':
    try:
        print('Starting polling...')
        bot.infinity_polling()
    except Exception as exc:
        print('Polling failed')
        print(exc)

import time
import pika


def get_pika_connection(host):
    print('Trying to connect to RabbitMQ...')
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host))
        print('RabbitMQ connection established')
        return connection
    except Exception as exc:
        print('Connection to RabbitMQ failed')
        print(exc)
        print('Waiting 3 seconds to retry')
        time.sleep(3)
        return get_pika_connection(host)


def publish_message(channel, queue, body):
    try:
        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=body
        )
    except Exception as exc:
        print(f'Publish to {queue} failed')
        print(exc)
        return False
    else:
        print(f'Payload to {queue} successfully sent')
        return True

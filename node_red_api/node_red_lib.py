import requests
from django.conf import settings
from urllib.parse import urljoin


def send_message_to_nr(chat_id, text_message):

    response = requests.get(
        urljoin(settings.NODE_API_ENDPOINT, 'send'),
        params={
            'chat_id': chat_id,
            'text': text_message.replace('&', ' '),
        }
    )
    response.raise_for_status()


def send_message_to_tg(chat_id, text_message):

    response = requests.get(
        f'https://api.telegram.org/bot{settings.TG_TOKEN}/sendMessage',
        params={
            'chat_id': chat_id,
            'text': text_message,
        }
    )
    response.raise_for_status()

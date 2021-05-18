import requests

from django.conf import settings
from urllib.parse import urljoin, urlencode


def send_message_to_nr(chat_id, message):
    url = urljoin(settings.NODE_API_ENDPOINT, 'send')

    text_message = str.replace(''.join(message), '&', '\n')

    query = {
        'chat_id': chat_id,
        'text': text_message,
    }

    response = requests.get(url, params=urlencode(query))
    response.raise_for_status()


def send_message_to_tg(chat_id, message):
    url = f'https://api.telegram.org/bot{settings.TG_TOKEN}/sendMessage'

    text_message = str.replace(''.join(message), '&', '\n')

    query = {
        'chat_id': chat_id,
        'text': text_message,
    }

    response = requests.get(url, params=urlencode(query))
    response.raise_for_status()

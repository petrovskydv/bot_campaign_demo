from urllib.parse import urljoin

import click
import requests


API_ENDPOINT = 'http://46.101.245.26:11880/api/'


def send_text(chat_id, text):
    url = urljoin(API_ENDPOINT, 'send')

    params = {
        'chat_id': chat_id,
        'text': text,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()


@click.command()
@click.argument('chat-id')
@click.argument('text')
def main(chat_id, text):
    send_text(chat_id, text)


if __name__ == '__main__':
    main()

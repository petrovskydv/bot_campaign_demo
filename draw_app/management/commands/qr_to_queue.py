from urllib.parse import urljoin

import django_rq
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from fns_open_api.bill_check import fetch_bill_check_info


FNS_STATUS_OK = 2


def send_telegram_text_message(chat_id, text):
    url = urljoin(settings.NODE_API_ENDPOINT, 'send')

    params = {
        'chat_id': chat_id,
        'text': text,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()


def get_fns_responce_receipt_items(qr_recognized):
    bill_check_info = fetch_bill_check_info(
        qr_recognized,
        settings.INN,
        settings.CLIENT_SECRET,
        settings.PASSWORD
    )
    
    if bill_check_info.get('status') == FNS_STATUS_OK:
        receipt_items = bill_check_info['ticket']['document']['receipt']['items']
        return receipt_items


def format_receipt_items_names(receipt_items):
    return ', '.join(item['name'] for item in receipt_items)


def handle_fns_request(chat_id, qr_recognized):
    receipt_items = get_fns_responce_receipt_items(qr_recognized)

    if receipt_items:
        items_names = format_receipt_items_names(receipt_items)
        message = f'Список ваших покупок: {items_names}'
        send_telegram_text_message(chat_id, message)
        return

    send_telegram_text_message(chat_id, 'Ваш чек не очень)')


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'chat_id',
            type=str,
            help='Telegram chat id'
        )
        parser.add_argument(
            'qr',
            type=str,
            help='Recognized QR code'
        )

    def handle(self, *args, **options):
        chat_id = options['chat_id']
        qr_recognized = options['qr']
        django_rq.enqueue(handle_fns_request, chat_id, qr_recognized)

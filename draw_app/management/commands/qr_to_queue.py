from urllib.parse import urljoin

import requests
from django_rq import job
from django.conf import settings
from django.core.management.base import BaseCommand
from rq import Retry

from fns_open_api.bill_check import fetch_bill_check


FNS_STATUS_OK = 2
FNS_STATUS_WRONG_QR = 8
RETRY_COUNT = 3
RETRY_INTERVALS = [60, 60*60, 60*60*24]


class FnsQRError(Exception):
    pass

class FnsNoDataYetError(Exception):
    pass


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
    bill_check_info = fetch_bill_check(
        qr_recognized,
        settings.INN,
        settings.CLIENT_SECRET,
        settings.PASSWORD
    )

    if bill_check_info.get('status') == FNS_STATUS_OK:
        receipt_items = bill_check_info['ticket']['document']['receipt']['items']
        return receipt_items

    if bill_check_info.get('status') == FNS_STATUS_WRONG_QR:
        raise FnsQRError

    #TODO: Добавить проверки остальных возможных статусов

    # Если qr-код валидный, но данных еще нет, то
    # скрипт упадет и RQ поставит его в конец очереди:
    raise FnsNoDataYetError


def format_receipt_items_names(receipt_items):
    return ', '.join(item['name'] for item in receipt_items)


@job('default', retry=Retry(max=RETRY_COUNT, interval=RETRY_INTERVALS))
def handle_fns_request(chat_id, qr_recognized):
    try:
        receipt_items = get_fns_responce_receipt_items(qr_recognized)
        items_names = format_receipt_items_names(receipt_items)
        message = f'Список ваших покупок: {items_names}'
    except FnsQRError:
        message = 'Ваш QR-код мы распознали, но похоже, что он не от чека с покупками.'

    send_telegram_text_message(chat_id, message)


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
        handle_fns_request.delay(chat_id, qr_recognized)

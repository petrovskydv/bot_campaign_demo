import sys
import json
import click
import requests

from environs import Env
from contextlib import contextmanager

from .irkkt_lib import (
    get_session_id, get_bill_check_id, get_bill_check_info
)

from draw_app.custom_exceptions import FnsQRError, FnsNoDataYetError

FNS_STATUS_OK = 2
FNS_STATUS_WRONG_QR = 8


@contextmanager
def handle_errors(inn, client_secret, password):

    if not inn:
        sys.exit('OS environments not content "INN"')
    if not client_secret:
        sys.exit('OS environments not content "CLIENT_SECRET"')
    if not password:
        sys.exit('OS environments not content "PASSWORD"')

    try:
        yield
    except requests.exceptions.HTTPError as error:
        print(error)


def get_fns_responce_receipt_items(qr_code, inn, client_secret, password):
    bill_check_info = fetch_bill_check(
        qr_code,
        inn,
        client_secret,
        password
    )

    if bill_check_info.get('status') == FNS_STATUS_OK:
        receipt_items = bill_check_info['ticket']['document']['receipt']['items']
        return receipt_items

    if bill_check_info.get('status') == FNS_STATUS_WRONG_QR:
        raise FnsQRError

    # TODO: Добавить проверки остальных возможных статусов

    # Если qr-код валидный, но данных еще нет, то
    # скрипт упадет и RQ поставит его в конец очереди:
    raise FnsNoDataYetError


def format_receipt_items(receipt_items, to_dict=False):
    if to_dict:
        return {num: item for num, item in enumerate(receipt_items, 1)}
    return ', '.join(item['name'] for item in receipt_items)


def fetch_bill_check(qr_code, inn, client_secret, password):
    session_id = get_session_id(inn, client_secret, password)
    bill_check_id = get_bill_check_id(session_id, qr_code)
    return get_bill_check_info(bill_check_id, session_id)


@click.command()
@click.option('-t', prompt='timestamp, время, когда вы осуществили покупку')
@click.option('-s', prompt='сумма чека')
@click.option('-fn', prompt='кодовый номер fss')
@click.option('-i', prompt='номер чека')
@click.option('-fp', prompt='параметр fiscalsign')
@click.option('-qr', required=False, help='qr код')
def main(t, s, fn, i, fp, qr):
    env = Env()
    env.read_env()

    inn = env.str('INN', '')
    client_secret = env.str('CLIENT_SECRET', '')
    password = env.str('PASSWORD', '')
    with handle_errors(inn, client_secret, password):
        qr_code = qr if qr else f't={t}&s={s}&fn={fn}&i={i}&fp={fp}&n=1'
        bill_check = fetch_bill_check(
            qr_code, inn, client_secret, password
        )
        print(json.dumps(bill_check, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()

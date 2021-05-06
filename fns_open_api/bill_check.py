import os
import sys
import json
import click
import requests

from dotenv import load_dotenv
from contextlib import contextmanager

from .irkkt_lib import (
    get_session_id, get_bill_check_id, get_bill_check_info
)


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


@click.command()
@click.option('-t', prompt='timestamp, время, когда вы осуществили покупку')
@click.option('-s', prompt='сумма чека')
@click.option('-fn', prompt='кодовый номер fss')
@click.option('-i', prompt='номер чека')
@click.option('-fp', prompt='параметр fiscalsign')
@click.option('-qr', required=False, help='qr код')
def main(t, s, fn, i, fp, qr):
    load_dotenv()

    inn = os.getenv('INN')
    client_secret = os.getenv('CLIENT_SECRET')
    password = os.getenv('PASSWORD')
    with handle_errors(inn, client_secret, password):
        qr_code = qr if qr else f't={t}&s={s}&fn={fn}&i={i}&fp={fp}&n=1'
        session_id = get_session_id(inn, client_secret, password)
        bill_check_id = get_bill_check_id(session_id, qr_code)
        bill_check_info = get_bill_check_info(bill_check_id, session_id)
        print(json.dumps(bill_check_info, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()

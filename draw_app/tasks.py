import functools
import requests
import time

from django.conf import settings

from django_rq import job
from dbr import (
    BarcodeReader,
    BarcodeReaderError
)

from qr_codes_recognition.barcode_reader import (
    init_runtime_settings,
    set_barcode_format,
    decode_file_stream
)

from fns_open_api.bill_check import (
    get_fns_responce_receipt_items,
    format_receipt_items,
)
from node_red_api.node_red_lib import send_message_to_tg
from draw_app.custom_exceptions import (
    ServiceNotRespond, QrCodeNoDataError,
    FnsQRError, FnsNoDataYetError
)


def time_it(temple_response):
    def wrap(func):
        @functools.wraps(func)
        def run_func(chat_id, image):
            start_time = time.time()
            result = func(chat_id, image)
            send_message_to_tg(
                chat_id,
                f'{temple_response}: {round((time.time() - start_time) * 1000, 2)} ms'
            )
            return result
        return run_func
    return wrap


@job('default')
@time_it('время распознования')
def handle_image(chat_id, image):

    try:
        reader = BarcodeReader()
        reader.init_license(settings.DYNAM_LICENSE_KEY)

        init_runtime_settings(reader, settings.RECOGNITION_QUALITY)
        set_barcode_format(reader, settings.BARCODE_FORMAT)

        barcode = decode_file_stream(reader, image)

    except (BarcodeReaderError, QrCodeNoDataError):
        send_message_to_tg(
            chat_id,
            '''Ошибка распознавания QR-кода, проверьте загруженное изображение
               и по возможности сфотографируйте заново.'''
        )
        raise
    except (requests.HTTPError, requests.ConnectionError):
        raise ServiceNotRespond('Сервис в данный момент не доступен.')

    if barcode:
        send_message_to_tg(chat_id, barcode)
        return barcode


@job('default')
@time_it('время получения ответа фнс')
def handle_barcode(chat_id, qrcode):

    try:
        receipt_items = get_fns_responce_receipt_items(
            qrcode, settings.INN,
            settings.CLIENT_SECRET,
            settings.PASSWORD
        )
        items_names = format_receipt_items(receipt_items, to_dict=True)

    except (FnsQRError, FnsNoDataYetError):
        send_message_to_tg(
            chat_id,
            'Ваш QR-код мы распознали, но похоже, что он не от чека с покупками.'
        )
        raise
    except (requests.HTTPError, requests.ConnectionError):
        raise ServiceNotRespond('Сервис в данный момент не доступен.')

    if items_names:
        send_message_to_tg(
            chat_id,
            f'Список ваших покупок: {items_names}'
        )
        return items_names

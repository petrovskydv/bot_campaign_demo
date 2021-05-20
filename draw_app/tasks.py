import re
import functools
import requests

from django.conf import settings
from django.utils.timezone import now

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
    FnsQRError, FnsNoDataYetError, QrCodeNotValidError
)

from .models import (
    User, QRCodeRecognitionAttempt
)


def handle_recognition_attempt(request_to):
    def wrap(func):
        @functools.wraps(func)
        def run_func(chat_id, object, *args):
            try:
                error_message = ''
                receipt, _ = args
                recognition_attempt = QRCodeRecognitionAttempt.objects.create(
                    receipt=receipt, request_to=request_to, start_time=now()
                )
                result = func(chat_id, object)
                recognition_attempt.end_time = now()
            except (BarcodeReaderError, QrCodeNoDataError):
                error_message = r'''
                Ошибка распознавания QR-кода, проверьте загруженное изображение и
                по возможности сфотографируйте заново.'''
                raise
            except (FnsQRError, FnsNoDataYetError, QrCodeNotValidError):
                error_message = r'''
                Ваш QR-код мы распознали, но похоже, что он не от чека с покупками.'''
                raise
            except (requests.HTTPError, requests.ConnectionError):
                error_message = 'Сервис в данный момент не доступен.'
                raise ServiceNotRespond()
            finally:
                if error_message:
                    recognition_attempt.reason_for_failure = error_message
                    send_message_to_tg(chat_id, error_message)
                recognition_attempt.save()
            return result
        return run_func
    return wrap


def get_valid_barcode(barcodes):
    pattern = r'''^t=[0-9A-Z]*&s=[0-9.]*&fn=[0-9]*&i=[0-9]*&fp=[0-9]*&n=[1-9]'''
    for barcode in barcodes:
        if re.search(pattern, barcode):
            return barcode
    raise QrCodeNotValidError('There is`t a valid barcode')


@job('default')
@handle_recognition_attempt('dynamsoft')
def handle_image(chat_id, image, *args):

    recognition_quality_setting = User.objects.filter(
        is_superuser=True
    ).first().qr_setting

    reader = BarcodeReader()
    reader.init_license(settings.DYNAM_LICENSE_KEY)

    init_runtime_settings(reader, recognition_quality_setting)
    set_barcode_format(reader, settings.BARCODE_FORMAT)

    barcodes = decode_file_stream(reader, image)

    if barcodes:
        return get_valid_barcode(barcodes)


@job('default')
@handle_recognition_attempt('fns_api')
def handle_barcode(chat_id, qrcode, *args):

    receipt_items = get_fns_responce_receipt_items(
        qrcode, settings.INN,
        settings.CLIENT_SECRET,
        settings.PASSWORD
    )
    items_names = format_receipt_items(receipt_items, to_dict=True)

    if items_names:
        send_message_to_tg(
            chat_id, f'Список ваших покупок: {items_names}'
        )
        return items_names

import re
import functools
import requests

from django.conf import settings
from django.utils.timezone import now
from django.db import transaction
from django_rq import job
from dbr import (
    BarcodeReader,
    BarcodeReaderError
)
from more_itertools import first
from rq import Retry

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
    User, Receipt, FnsOrder, ReceiptRecognitionOuterRequestStat
)

RETRY_COUNT = 3
RETRY_INTERVALS = [10, 30, 60]


def handle_recognition_attempt(request_to):
    def wrap(func):
        @functools.wraps(func)
        def run_func(chat_id, *args):
            try:
                error_message = ''
                quality_setting = User.objects.filter(
                    is_superuser=True
                ).first().qr_setting
                recognition_attempt = ReceiptRecognitionOuterRequestStat.objects.create(
                    receipt=Receipt.objects.get(id=first(*args)),
                    request_to=request_to,
                    dynamsoft_quality_setting=(
                        quality_setting if request_to == 'dynamsoft' else ''
                    )
                )
                result = func(
                    chat_id, *args, quality_setting=quality_setting
                )
                recognition_attempt.end_time = now()
            except Receipt.DoesNotExist:
                error_message = r'''Чек отсутствует или удален в базе данных.'''
            except FnsOrder.DoesNotExist:
                error_message = r'''
                Заказ в налоговую отсутствует или удален в базе данных.'''
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


@transaction.atomic
def update_qr_recognized(barcode, receipt_and_order_ids):
    receipt_id, order_id = receipt_and_order_ids
    receipt = Receipt.objects.get(id=receipt_id)
    order = FnsOrder.objects.get(id=order_id)
    receipt.qr_recognized = barcode
    receipt.save()
    order.сheck_ticket_info = barcode
    order.status = 'sent'
    order.save()


@transaction.atomic
def update_fns_answer(fns_answer, receipt_and_order_ids):
    _, order_id = receipt_and_order_ids
    order = FnsOrder.objects.get(id=order_id)
    order.answer = fns_answer
    order.status = 'received'
    order.save()


@job('default', retry=Retry(max=RETRY_COUNT, interval=RETRY_INTERVALS))
@handle_recognition_attempt('dynamsoft')
def handle_image(chat_id, *args, **options):

    image = Receipt.objects.get(id=first(*args)).image
    reader = BarcodeReader()
    reader.init_license(settings.DYNAM_LICENSE_KEY)

    init_runtime_settings(reader, options['quality_setting'])
    set_barcode_format(reader, settings.BARCODE_FORMAT)

    barcodes = decode_file_stream(
        reader, open(image.path, "rb").read()
    )

    if barcodes:
        valid_barcode = get_valid_barcode(barcodes)
        update_qr_recognized(valid_barcode, *args)
        return valid_barcode


@job('default', retry=Retry(max=RETRY_COUNT, interval=RETRY_INTERVALS))
@handle_recognition_attempt('fns_api')
def handle_barcode(chat_id, *args, **options):

    qrcode = Receipt.objects.get(id=first(*args)).qr_recognized
    receipt_items = get_fns_responce_receipt_items(
        qrcode, settings.INN,
        settings.CLIENT_SECRET,
        settings.PASSWORD
    )
    items_names = format_receipt_items(receipt_items, to_dict=True)

    if items_names:
        update_fns_answer(items_names, *args)
        send_message_to_tg(
            chat_id, f'Список ваших покупок: {items_names}'
        )
        return items_names

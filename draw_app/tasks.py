import re
import requests
import functools
import contextlib
import textwrap

from datetime import timedelta
from django.conf import settings
from django.utils.timezone import now
from django.db import transaction
from django_rq import job, get_queue
from dbr import (
    BarcodeReader,
    BarcodeReaderError
)
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
from node_red_api.node_red_lib import send_message_to_nr
from draw_app.extra_functools import suppress
from draw_app.custom_exceptions import (
    QrCodeNoDataError, FnsQRError, FnsNoDataYetError,
    QrCodeNotValidError, QualitySettingNotFilled
)

from .models import (
    Customer, Receipt, FnsOrder, ReceiptRecognitionOuterRequestStat
)

RETRY_COUNT = 3
RETRY_INTERVALS = [60, 3600, 86400]


@contextlib.contextmanager
def create_recognition_attempt(receipt_id, request_to):
    recognition_attempt = ReceiptRecognitionOuterRequestStat.objects.create(
        receipt=Receipt.objects.get(id=receipt_id),
        request_to=request_to
    )
    try:
        yield recognition_attempt
    except (
        BarcodeReaderError, QrCodeNoDataError,
        FnsQRError, FnsNoDataYetError, QrCodeNotValidError,
        requests.HTTPError, requests.ConnectionError,
        Receipt.DoesNotExist, FnsOrder.DoesNotExist,
        QualitySettingNotFilled
    ) as exc:
        error_message = repr_exceptions(exc)
        recognition_attempt.reason_for_failure = error_message
        raise
    finally:
        recognition_attempt.save()


def repr_exceptions(exc):
    if isinstance(exc, (BarcodeReaderError, QrCodeNoDataError)):
        return textwrap.dedent(r'''
        Ошибка распознавания QR-кода, проверьте загруженное изображение и
        по возможности сфотографируйте заново.
        ''')
    elif isinstance(exc, FnsQRError):
        return textwrap.dedent(r'''
        Ваш QR-код мы распознали, но информация на нем,
        не соответствует полученной из налогового органа.
        ''')
    elif isinstance(exc, FnsNoDataYetError):
        return r'''
        Ваш QR-код мы распознали, но в налоговой еще нет информации о нем.'''
    elif isinstance(exc, QrCodeNotValidError):
        return r'''
        Ваш QR-код мы распознали, но похоже, что он не от чека с покупками.'''
    elif isinstance(exc, QualitySettingNotFilled):
        return r'''Не заполнена настройка качества распознавания QR-кодов.'''
    elif isinstance(exc, (requests.HTTPError, requests.ConnectionError)):
        return r'''Сервис в данный момент не доступен.'''
    elif isinstance(exc, Receipt.DoesNotExist):
        return r'''Чек отсутствует или удален в базе данных.'''
    elif isinstance(exc, FnsOrder.DoesNotExist):
        return r'''Заказ в налоговую отсутствует или удален в базе данных.'''


def handle_recognition_attempt(request_to):
    def wrap(func):
        @functools.wraps(func)
        def run_func(chat_id, receipt_id, order_id):
            with create_recognition_attempt(receipt_id, request_to) as recognition_attempt:
                result = func(
                    chat_id, receipt_id, order_id, current_attempt=recognition_attempt
                )
                recognition_attempt.end_time = now()
            return result
        return run_func
    return wrap


def launch_user_notification(request_to):
    def wrap(func):
        @functools.wraps(func)
        def run_func(chat_id, receipt_id, order_id):
            try:
                func(chat_id, receipt_id, order_id)
            except: # noqa
                raise
            finally:
                current_queue = get_queue()
                if request_to == 'dynamsoft':
                    current_queue.enqueue_in(
                        timedelta(seconds=1), report_recognized_qr_code, chat_id, receipt_id, order_id
                    )
                if request_to == 'fns_api':
                    current_queue.enqueue_in(
                        timedelta(seconds=1), report_fns_api, chat_id, receipt_id, order_id
                    )
        return run_func
    return wrap


def get_valid_barcode(barcodes):
    pattern = r'''^t=[0-9A-Z]*&s=[0-9.]*&fn=[0-9]*&i=[0-9]*&fp=[0-9]*&n=[1-9]'''
    for barcode in barcodes:
        if re.search(pattern, barcode):
            return barcode
    raise QrCodeNotValidError()


@transaction.atomic
def update_qr_recognized(barcode, receipt_id, order_id):
    receipt = Receipt.objects.get(id=receipt_id)
    order = FnsOrder.objects.get(id=order_id)
    receipt.qr_recognized = barcode
    receipt.save()
    order.сheck_ticket_info = barcode
    order.status = 'sent'
    order.qr_recognized = barcode
    order.save()


@transaction.atomic
def update_fns_answer(fns_answer, order_id):
    order = FnsOrder.objects.get(id=order_id)
    order.answer = fns_answer
    order.status = 'received'
    order.save()


@job('default', retry=Retry(max=RETRY_COUNT, interval=RETRY_INTERVALS))
@suppress(Receipt.DoesNotExist, FnsOrder.DoesNotExist)
@launch_user_notification('dynamsoft')
@handle_recognition_attempt('dynamsoft')
def handle_image(chat_id, receipt_id, order_id, **options):
    valid_barcode = ''

    quality_setting = Customer.objects.get(tg_chat_id=chat_id).quality_setting
    if not quality_setting:
        raise QualitySettingNotFilled()

    if options.get('current_attempt'):
        options['current_attempt'].dynamsoft_quality_setting = quality_setting

    image = Receipt.objects.get(id=receipt_id).image
    reader = BarcodeReader()
    reader.init_license(settings.DYNAM_LICENSE_KEY)

    init_runtime_settings(reader, quality_setting)
    set_barcode_format(reader, settings.BARCODE_FORMAT)

    with open(image.path, "rb") as image_handler:
        barcodes = decode_file_stream(
            reader, image_handler.read()
        )

    valid_barcode = get_valid_barcode(barcodes)
    update_qr_recognized(valid_barcode, receipt_id, order_id)


@job('default', retry=Retry(max=RETRY_COUNT, interval=RETRY_INTERVALS))
@suppress(Receipt.DoesNotExist, FnsOrder.DoesNotExist)
@launch_user_notification('fns_api')
@handle_recognition_attempt('fns_api')
def handle_barcode(chat_id, receipt_id, order_id, **options):

    qrcode = Receipt.objects.get(id=receipt_id).qr_recognized
    receipt_items = get_fns_responce_receipt_items(
        qrcode, settings.INN,
        settings.CLIENT_SECRET,
        settings.PASSWORD
    )
    items_names = format_receipt_items(receipt_items, to_dict=True)

    if items_names:
        update_fns_answer(items_names, order_id)


def handle_failed_attempts(chat_id, receipt_id, request_to):
    sent_notifications = \
        ReceiptRecognitionOuterRequestStat.objects.sent_notifications().filter(
            receipt__id=receipt_id, request_to=request_to
        ).values_list('reason_for_failure')

    failed_attempts = ReceiptRecognitionOuterRequestStat.objects.failed().filter(
        receipt__id=receipt_id, request_to=request_to
    ).exclude(reason_for_failure__in=sent_notifications)

    failed_attempt = failed_attempts.first()
    if not failed_attempt:
        return True

    reason_for_failure = failed_attempt.reason_for_failure
    test_message = ''
    if request_to == 'dynamsoft':
        test_message = \
            textwrap.dedent(f'''
            Попытка распознавания чека {failed_attempt.receipt}:
            Статус распознавания: {reason_for_failure}.
            ''')
    elif request_to == 'fns_api':
        test_message = \
            textwrap.dedent(f'''
            Попытка отправки в ФНС для чека {failed_attempt.receipt}:
            Статус ответа из ФНС: {reason_for_failure}.
            ''')

    if test_message:
        send_message_to_nr(chat_id, test_message)

    failed_attempts.update(sent_notification=True)
    return True


@job('default')
@suppress(Receipt.DoesNotExist, ReceiptRecognitionOuterRequestStat.DoesNotExist)
def report_recognized_qr_code(chat_id, receipt_id, order_id, **options):
    recognized_code = Receipt.objects.get(id=receipt_id).qr_recognized

    if not recognized_code:
        return handle_failed_attempts(chat_id, receipt_id, 'dynamsoft')

    recognized_status = 'qr код успешно распознан'
    dynamsoft_attempt = \
        ReceiptRecognitionOuterRequestStat.objects.successful().filter(
            receipt__id=receipt_id, request_to='dynamsoft'
        ).get()
    recognized_time = (dynamsoft_attempt.end_time - dynamsoft_attempt.start_time)
    text_message = textwrap.dedent(f'''
    - Статус распознавания: {recognized_status},
    {recognized_code}
    - Время распознавания qr кода: {recognized_time.seconds}.{recognized_time.microseconds},
    ''')
    send_message_to_nr(chat_id, text_message)


@job('default')
@suppress(FnsOrder.DoesNotExist, ReceiptRecognitionOuterRequestStat.DoesNotExist)
def report_fns_api(chat_id, receipt_id, order_id, **options):
    fns_answer = FnsOrder.objects.get(id=order_id).answer

    if not fns_answer:
        return handle_failed_attempts(chat_id, receipt_id, 'fns_api')

    fns_api_attempt = \
        ReceiptRecognitionOuterRequestStat.objects.successful().filter(
            receipt__id=receipt_id, request_to='fns_api'
        ).get()
    recognized_time = (fns_api_attempt.end_time - fns_api_attempt.start_time)

    product_list = "\n".join([
        f'-{item["name"]}  {item["quantity"]}  {item["price"]/100}' for _, item in fns_answer.items()
    ])

    text_message = textwrap.dedent(f'''
    - Результат запроса в налоговую:
    {product_list},
    - Время получения ответа ФНС: {recognized_time.seconds}.{recognized_time.microseconds}
    ''')
    send_message_to_nr(chat_id, text_message)
    send_message_to_nr(chat_id, f'{fns_answer}')

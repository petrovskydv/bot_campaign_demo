from contextlib import contextmanager, suppress

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from dbr import (
    BarcodeReader,
    BarcodeReaderError
)

from draw_app.models import FnsOrder
from draw_app.notify_rollbar import notify_rollbar
from qr_codes_recognition.barcode_reader import (
    init_runtime_settings,
    set_barcode_format,
    decode_file_stream
)

from draw_app.models import User


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--img', nargs='?', type=str,
            help='путь к изображению для сканирования qr-кодов'
        )

    def handle(self, *args, **options):
        with suppress(KeyboardInterrupt):
            read_barcodes(options)

    def execute(self, *args, **options):
        with notify_rollbar():
            return super().execute(*args, **options)


@contextmanager
def handle_errors():
    try:
        yield
    except BarcodeReaderError as error:
        raise CommandError(error)


def read_barcodes(options):
    qr_codes = []
    if options.get('img'):
        with open(options.get('img'), "rb") as file_handler:
            # Список здесь нужен т.к. на одном чеке может быть несколько баркодов
            qr_codes.extend(read_barcode(options, file_handler.read()))
    else:
        raw_orders = FnsOrder.objects.raw().select_related('receipt').all()
        for raw_order in raw_orders:
            with handle_errors():
                image_in_bytes = open(raw_order.receipt.image.path, "rb").read()
                qr_codes.extend(read_barcode(options, image_in_bytes))
    # TODO Заглушка. Здесь обработка записи распознанных кодов в базу данных
    print(qr_codes)


def read_barcode(options, image):

    reader = BarcodeReader()
    reader.init_license(settings.DYNAM_LICENSE_KEY)

    recognition_quality_setting = User.objects.filter(
        is_superuser=True
    ).first().qr_setting

    init_runtime_settings(reader, recognition_quality_setting)
    set_barcode_format(reader, settings.BARCODE_FORMAT)

    return decode_file_stream(reader, image)

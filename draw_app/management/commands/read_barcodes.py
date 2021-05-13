import functools
from contextlib import contextmanager, suppress
from lucky_draws.settings import STATIC_ROOT

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from dbr import (
    BarcodeReader,
    BarcodeReaderError
)

from draw_app.models import FnsOrder
from qr_codes_recognition.barcode_reader import (
    init_runtime_settings,
    set_barcode_format,
    decode_file
)
from draw_app.notify_rollbar import notify_rollbar


class ScanFinish(Exception):
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--img', nargs='?', type=str,
            help='путь к каталогу с изображениями для сканирования qr-кодов'
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


def handle_images():
    def wrap(func):
        @functools.wraps(func)
        def run_func(options):
            qr_codes = []
            if options.get('img'):
                qr_codes.extend(func(options, options.get('img')))
            else:
                raw_orders = FnsOrder.objects.raw().select_related('receipt').all()
                for raw_order in raw_orders:
                    with handle_errors():
                        qr_codes.extend(func(options, raw_order.receipt.image.path))
            # TODO Заглушка. Здесь обработка записи распознанных кодов в базу данных
            print(qr_codes)
        return run_func
    return wrap


@handle_images()
def read_barcodes(options, image_path):

    reader = BarcodeReader()
    reader.init_license(settings.DYNAM_LICENSE_KEY)

    init_runtime_settings(reader, settings.RECOGNITION_QUALITY, STATIC_ROOT)
    set_barcode_format(reader, settings.BARCODE_FORMAT, STATIC_ROOT)

    return decode_file(reader, image_path)

import asyncio
import functools
import requests

from contextlib import suppress
from anyio import create_task_group, run, open_cancel_scope
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from draw_app.models import FnsOrder
from fns_open_api.bill_check import fetch_bill_check_info
from draw_app.notify_rollbar import notify_rollbar


class SwapFinish(Exception):
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--qr', nargs='?', type=str,
            help='QRCODE для обмена с базой данных налоговой инспекции РФ'
        )

    def handle(self, *args, **options):
        with suppress(KeyboardInterrupt):
            run(run_swapping, options)

    def execute(self, *args, **options):
        with notify_rollbar():
            return super().execute(*args, **options)


def handle_errors():
    def wrap(func):
        @functools.wraps(func)
        async def run_func(queue):
            while True:
                try:
                    await func(queue)
                except requests.HTTPError:
                    # TODO логика обработки ошибки анализа qr кода на сайте налоговой
                    raise CommandError("Ошибка анализа qr кода")
                except requests.ConnectionError:
                    await asyncio.sleep(60)
                    continue
                except SwapFinish as message:
                    # временная заглушка, пока не добавлена логика работы с успешно полученным чеком из фнс
                    print(message)
                    break
        return run_func
    return wrap


async def run_swapping(options):

    qrcode = options.get('qr')
    request_queue = asyncio.Queue()

    async with create_task_group() as task_group:
        if qrcode:
            # временно для целей тестирования асинхронной очереди
            await task_group.spawn(update_tax_request_test, request_queue, qrcode)
            await task_group.spawn(fetch_tax_data_test, request_queue)
        else:
            await task_group.spawn(update_tax_requests, request_queue)
            await task_group.spawn(fetch_tax_data, request_queue)


@sync_to_async
def fetch_raw_fns_orders():
    raw_tax_requests = FnsOrder.objects.raw()
    return [
        *raw_tax_requests,
    ]


async def update_tax_request(request_queue, raw_fns_order):
    request_queue.put_nowait(raw_fns_order)
    await request_queue.join()


@handle_errors()
async def update_tax_requests(request_queue):

    raw_fns_orders = await fetch_raw_fns_orders()
    async with create_task_group() as update_tax_group:
        for raw_fns_order in raw_fns_orders:
            await update_tax_group.spawn(
                update_tax_request, request_queue, raw_fns_order
            )


@handle_errors()
async def fetch_tax_data(request_queue):

    tax_request = await request_queue.get()
    if tax_request.qr_recognized:
        bill_check_info = fetch_bill_check_info(
            tax_request.qr_recognized, settings.INN,
            settings.CLIENT_SECRET, settings.PASSWORD
        )
        tax_request.answer = bill_check_info
        async with open_cancel_scope(shield=True):
            await sync_to_async(tax_request.save)()

    request_queue.task_done()


async def update_tax_request_test(request_queue, qrcode):

    request_queue.put_nowait(qrcode)
    await request_queue.join()


@handle_errors()
async def fetch_tax_data_test(request_queue):

    qrcode = await request_queue.get()

    if qrcode:
        bill_check_info = fetch_bill_check_info(
            qrcode, settings.INN,
            settings.CLIENT_SECRET, settings.PASSWORD
        )

    request_queue.task_done()
    raise SwapFinish(bill_check_info)

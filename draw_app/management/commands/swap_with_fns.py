import asyncio

from contextlib import suppress
from anyio import create_task_group, run, open_cancel_scope
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


from draw_app.models import FnsOrder
from fns_open_api import fetch_bill_check_info
from draw_app.notify_rollbar import notify_rollbar


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--swap',
            action='store_true',
            help='Запускает обмен чеками с базой данных налоговой инспекции РФ'
        )

    def handle(self, *args, **options):
        with suppress(KeyboardInterrupt):
            run(run_swapping, options)

    def execute(self, *args, **options):
        with notify_rollbar():
            return super().execute(*args, **options)


async def run_swapping(options):

    if not options['track']:
        raise CommandError('Disable swapping with tax office.')

    tax_request_queue = asyncio.Queue

    async with create_task_group as task_group:
        await task_group.spawn(update_tax_requests, tax_request_queue)
        await task_group.spawn(fetch_tax_data, tax_request_queue)


@sync_to_async
def select_raw_tax_requests():
    raw_tax_requests = (
        FnsOrder.objects
        .filter(
            answer__isnull=True
        )
    )
    return [
        *raw_tax_requests,
    ]


async def update_tax_request(tax_request_queue, raw_tax_request):
    tax_request_queue.put_nowait(raw_tax_request)
    await tax_request_queue.join()


async def update_tax_requests(tax_request_queue):

    while True:

        raw_tax_requests = await select_raw_tax_requests()
        
        async with create_task_group() as update_tax_group:
            for raw_tax_request in raw_tax_requests:
                update_tax_group.spawn(
                    update_tax_request, tax_request_queue, raw_tax_request
                )


async def fetch_tax_data(tax_request_queue):

    while True:

        tax_request = tax_request_queue.get()
        if tax_request.qr_recognized:
            bill_check_info = fetch_bill_check_info(
                tax_request.qr_recognized, settings.INN,
                settings.CLIENT_SECRET, settings.PASSWORD
            )
            tax_request.answer = bill_check_info
            async with open_cancel_scope(shield=True):
                await sync_to_async(tax_request.save)()

        tax_request_queue.task_done()

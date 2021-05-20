import base64
import django_rq
import time

from django.db import transaction
from django.utils.timezone import now
from django.core.files.base import ContentFile
from rest_framework.response import Response
from rest_framework.decorators import api_view

from draw_app.notify_rollbar import notify_rollbar
from .tasks import handle_image, handle_barcode
from .custom_exceptions import (
    ServiceNotRespond,
    QrCodeNotValidError
)

from .models import (
    Customer, Receipt, FnsOrder
)


@transaction.atomic
def get_receipt_and_raw_order(chat_id, image):
    customer, create = Customer.objects.get_or_create(tg_chat_id=chat_id)
    if create:
        customer.date_joined = now()
        customer.save()

    receipt = Receipt.objects.create(uploaded_at=now(), customer=customer)
    receipt.image.save(
        f'{now().strftime("%Y%m%d%H%M%s")}.png', ContentFile(image)
    )
    fns_order, create = FnsOrder.objects.get_or_create(receipt=receipt, status='raw')
    return receipt, fns_order


@transaction.atomic
def update_qr_recognized(barcode_item, *args):
    receipt, order = args
    if barcode_item:
        receipt.qr_recognized = barcode_item
        receipt.save()
        order.first_requested_at = now()
        order.сheck_ticket_info = barcode_item
        order.status = 'sent'
        order.save()


@transaction.atomic
def update_fns_answer(fns_answer, *args):
    _, order = args
    if fns_answer:
        order.answer = fns_answer
        order.status = 'received'
        order.save()


def waiting_task_finish(current_task):
    while not current_task.result:
        time.sleep(0.1)


@api_view(['POST'])
def handle_receipt_image(request):
    try:
        with notify_rollbar():
            chat_id = request.data['chatId']
            image = base64.b64decode(request.data['content'])
            receipt_and_order = get_receipt_and_raw_order(chat_id, image)
            if receipt_and_order:
                queue = django_rq.get_queue('default')
                barcode = queue.enqueue(handle_image, chat_id, image, *receipt_and_order)
                waiting_task_finish(barcode)
                update_qr_recognized(barcode.result, *receipt_and_order)
                fns_answer = queue.enqueue(handle_barcode, chat_id, barcode.result, *receipt_and_order)
                waiting_task_finish(fns_answer)
                update_fns_answer(fns_answer.result, *receipt_and_order)
    except (ServiceNotRespond, QrCodeNotValidError) as error:
        return Response(f'fail: {error}')

    return Response('ok')

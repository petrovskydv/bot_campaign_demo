import base64

from django.db import transaction
from django.utils.timezone import now
from django.core.files.base import ContentFile
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.serializers import Serializer, CharField

from draw_app.notify_rollbar import notify_rollbar
from .tasks import (
    handle_image, handle_barcode,
    report_recognized_qr_code,
    report_fns_api,
    report_recognized_problems
)

from .models import (
    Customer, Receipt, FnsOrder
)


class ReceiptImageSerializer(Serializer):
    chatId = CharField()
    content = CharField()


@transaction.atomic
def get_or_create_customer(chat_id):
    customer, create = Customer.objects.get_or_create(tg_chat_id=chat_id)
    if create:
        customer.save()
    return customer


@transaction.atomic
def create_receipt_and_raw_order(customer, image):

    receipt = Receipt.objects.create(customer=customer)
    receipt.image.save(
        f'{now().strftime("%Y%m%d%H%M%s")}.png', ContentFile(image)
    )
    fns_order, _ = FnsOrder.objects.get_or_create(receipt=receipt, status='raw')
    return receipt.id, fns_order.id


@api_view(['POST'])
def handle_receipt_image(request):

    with notify_rollbar():
        serializer = ReceiptImageSerializer(data=request.data)
        if serializer.is_valid():
            chat_id = serializer.data['chatId']
            image = base64.b64decode(serializer.data['content'])
            current_customer = get_or_create_customer(chat_id)
            receipt_id, order_id = create_receipt_and_raw_order(current_customer, image)
            if receipt_id and order_id:
                handle_image_task = handle_image.delay(chat_id, receipt_id, order_id)
                handle_barcode_task = handle_barcode.delay(
                    chat_id, receipt_id, order_id, depends_on=handle_image_task
                )
                report_recognized_qr_code.delay(
                    chat_id, receipt_id, order_id, depends_on=handle_image_task
                )
                report_fns_api.delay(
                    chat_id, receipt_id, order_id, depends_on=handle_barcode_task
                )
                # TODO Доделать запуск функции с задержкой
                # report_recognized_problems.delay(chat_id, receipt_id, order_id, job_timeout=60)
            return JsonResponse({'replay': 'ok'}, status=200)
        return JsonResponse(serializer.errors, status=400)

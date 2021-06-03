import base64

from django.db import transaction
from django.utils.timezone import now
from django.core.files.base import ContentFile
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.serializers import Serializer, CharField

from .tasks import (
    handle_image, handle_fns_message_id, handle_get_purchases
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
    serializer = ReceiptImageSerializer(data=request.data)
    if serializer.is_valid():
        chat_id = serializer.data['chatId']
        image = base64.b64decode(serializer.data['content'])
        current_customer = get_or_create_customer(chat_id)
        receipt_id, order_id = create_receipt_and_raw_order(current_customer, image)
        if receipt_id and order_id:
            handle_image_task = handle_image.delay(chat_id, receipt_id, order_id)

            message_id_task = handle_fns_message_id.delay(
                chat_id, receipt_id, order_id,
                depends_on=handle_image_task
            )

            handle_get_purchases.delay(
                chat_id, receipt_id, order_id,
                depends_on=message_id_task
            )

        return JsonResponse({'replay': 'ok'}, status=200)
    return JsonResponse(serializer.errors, status=400)


@api_view(['GET'])
def handle_purchases(request, tg_chat_id):
    fns_orders = FnsOrder.objects.filter(
        receipt__customer__tg_chat_id=tg_chat_id,
    ).exclude(answer={})

    if not fns_orders:
        return JsonResponse({'purchases': 'Покупок пока нет'}, status=200)

    purchases = []

    for fns_order in fns_orders:
        content = fns_order.answer.get('content')

        if not content:
            continue

        for item in content['items']:
            purchases.append(
                f'🛒 {item["name"]}: {item["quantity"]} шт, {item["price"]/100} ₽'
            )

    return JsonResponse({'purchases': '\n'.join(purchases)}, status=200)

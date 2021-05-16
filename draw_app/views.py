import base64
import requests
from django.conf import settings
from dbr import (BarcodeReader, BarcodeReaderError)
from requests.models import HTTPError
from rest_framework.response import Response
from rest_framework.decorators import api_view

from urllib.parse import urljoin, urlencode

from draw_app.notify_rollbar import notify_rollbar
from qr_codes_recognition.barcode_reader import (
    init_runtime_settings,
    set_barcode_format,
    decode_file_stream
)


def read_barcode(image):
    reader = BarcodeReader()
    reader.init_license(settings.DYNAM_LICENSE_KEY)

    init_runtime_settings(reader, settings.RECOGNITION_QUALITY)
    set_barcode_format(reader, settings.BARCODE_FORMAT)

    return decode_file_stream(reader, image)


def send_to_front(chat_id, message):
    url = urljoin(settings.NODE_API_ENDPOINT, 'send')

    query = {
        'chat_id': chat_id,
        'text': str.replace(''.join(message), '&', '\n'),
    }

    response = requests.get(url, params=urlencode(query))
    response.raise_for_status()

    return response.json()


@api_view(['POST'])
def handle_receipt_image(request):
    try:
        with notify_rollbar():
            chat_id = request.data['chatId']
            image = base64.b64decode(request.data['content'])
            barcode = read_barcode(image)
            if barcode:
                send_to_front(chat_id, barcode)
    except HTTPError as error:
        return Response(f'fail: {error}')
    except BarcodeReaderError as error:
        return Response(f'fail: {error}')

    return Response('ok')

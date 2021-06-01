import base64
import json
import time
from urllib.parse import parse_qs

import redis
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from requests_toolbelt.adapters import source

from draw_app.custom_exceptions import (
    FnsGetTemporaryTokenError,
    FnsNoDataYetError,
    FnsQRError,
)


DELAY = 2
FNS_RESPONSE_COMPLETED = 'COMPLETED'
FNS_RESPONSE_PROCESSING = 'PROCESSING'

GET_TOKEN_XML = f'''
<soap:Envelope soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <soap:Body>
        <GetMessageRequest xmlns="urn://x-artefacts-gnivc-ru/inplat/servin/OpenApiMessageConsumerService/types/1.0">
            <Message>
                <tns:AuthRequest xmlns:tns="urn://x-artefacts-gnivc-ru/ais3/kkt/AuthService/types/1.0">
                    <tns:AuthAppInfo>
                        <tns:MasterToken>{settings.FNS_MASTER_TOKEN}</tns:MasterToken>
                    </tns:AuthAppInfo>
                </tns:AuthRequest>
            </Message>
        </GetMessageRequest>
    </soap:Body>
</soap:Envelope>
'''

GET_MESSAGE_ID_XML = '''
<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
	<soap-env:Body>
		<ns0:SendMessageRequest xmlns:ns0="urn://x-artefacts-gnivc-ru/inplat/servin/OpenApiAsyncMessageConsumerService/types/1.0">
			<ns0:Message>
				<tns:GetTicketRequest xmlns:tns="urn://x-artefacts-gnivc-ru/ais3/kkt/KktTicketService/types/1.0">
					<tns:GetTicketInfo>
						<tns:Sum>{s}</tns:Sum>
						<tns:Date>{t}</tns:Date>
						<tns:Fn>{fn}</tns:Fn>
						<tns:TypeOperation>{n}</tns:TypeOperation>
						<tns:FiscalDocumentId>{i}</tns:FiscalDocumentId>
						<tns:FiscalSign>{fp}</tns:FiscalSign>
						<tns:RawData>true</tns:RawData>
					</tns:GetTicketInfo>
				</tns:GetTicketRequest>
			</ns0:Message>
		</ns0:SendMessageRequest>
	</soap-env:Body>
</soap-env:Envelope>
'''

GET_PURCHASES_XML = '''
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="urn://x-artefacts-gnivc-ru/inplat/servin/OpenApiAsyncMessageConsumerService/types/1.0">
   <soapenv:Header/>
   <soapenv:Body>
      <ns:GetMessageRequest>
         <ns:MessageId>{message_id}</ns:MessageId>
      </ns:GetMessageRequest>
   </soapenv:Body>
</soapenv:Envelope>
'''


def get_session():
    session = requests.Session()
    interface = source.SourceAddressAdapter(settings.FNS_REQUEST_INTERFACE)
    session.mount('http://', interface)
    session.mount('https://', interface)

    return session


def get_fns_token(xml_body):
    headers = {
        'Content-Type': 'text/xml',
        'Accept-Charset': 'utf-8',
    }

    params = {
        'wsdl': ''
    }

    session = get_session()

    response = session.post(
        settings.FNS_AUTH_ENDPOINT,
        headers=headers,
        params=params,
        data=xml_body
    )

    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'xml')

    token = soup.find('Token')
    expired_at = soup.find('ExpireTime')

    if not all([token, expired_at]):
        raise FnsGetTemporaryTokenError

    return token.text, expired_at.text


def get_token_expired_sec(expired_at):
    now = timezone.now()
    return (parser.parse(expired_at) - now).seconds


def get_or_create_token():
    redis_settings = settings.RQ_QUEUES['default']

    r = redis.Redis(
        host = redis_settings['HOST'],
        port = redis_settings['PORT'],
        password = redis_settings['PASSWORD'],
        decode_responses=True
    )

    token = r.get(settings.FNS_TEMPORARY_TOKEN_REDIS_KEY)

    if not token:
        token, expired_at = get_fns_token(GET_TOKEN_XML)
        token_expired_sec = get_token_expired_sec(expired_at)
        r.set(settings.FNS_TEMPORARY_TOKEN_REDIS_KEY, token, token_expired_sec)

    return token


def prepare_message_id_request_xml(qr_recognized):
    parsed_keys = parse_qs(qr_recognized)

    xml = GET_MESSAGE_ID_XML.format(
        s=int(float(parsed_keys['s'][0]) * 100),
        t=parser.parse(parsed_keys['t'][0]).isoformat(),
        fn=parsed_keys['fn'][0],
        n=parsed_keys['n'][0],
        i=parsed_keys['i'][0],
        fp=parsed_keys['fp'][0],
    )

    return xml


def get_message_id(qr_recognized):
    headers = {
        'Content-Type': 'text/xml',
        'Accept-Charset': 'utf-8',
        'FNS-OpenApi-Token': get_or_create_token(),
        'FNS-OpenApi-UserToken': base64.b64encode(settings.FNS_APPID.encode()).decode()
    }

    params = {
        'wsdl': ''
    }

    session = get_session()

    response = session.post(
        settings.FNS_KKT_SERVICE_ENDPOINT,
        headers=headers,
        params=params,
        data=prepare_message_id_request_xml(qr_recognized)
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'xml')

    return soup.find('MessageId').text


def get_purchases(qr_recognized, message_id=None):
    if not message_id:
        message_id = get_message_id(qr_recognized)
        time.sleep(DELAY)

    headers = {
        'Content-Type': 'text/xml',
        'Accept-Charset': 'utf-8',
        'FNS-OpenApi-Token': get_or_create_token(),
        'FNS-OpenApi-UserToken': base64.b64encode(settings.FNS_APPID.encode()).decode()
    }

    params = {
        'wsdl': ''
    }

    session = get_session()
    response = session.post(
        settings.FNS_KKT_SERVICE_ENDPOINT,
        headers=headers,
        params=params,
        data=GET_PURCHASES_XML.format(message_id=message_id)
    )

    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'xml')
    status = soup.find('ProcessingStatus').text

    if status == FNS_RESPONSE_COMPLETED:
        code = soup.find('Code').text
        if code == '200':
            purchases = soup.find('Ticket').text
            return json.loads(purchases)

        raise FnsQRError

    if status == FNS_RESPONSE_PROCESSING:
        raise FnsNoDataYetError

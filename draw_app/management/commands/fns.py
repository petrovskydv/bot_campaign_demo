import requests
from requests_toolbelt.adapters import source
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand


XML_GET_TOKEN_BODY = f'''<soap:Envelope soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
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
</soap:Envelope>'''


class FnsError(Exception):
    pass


def get_fns_response(xml_body):
    headers = {
        'Content-Type': 'text/xml',
        'Accept-Charset': 'utf-8',
    }

    params = {
        'wsdl': ''
    }

    session = requests.Session()
    interface = source.SourceAddressAdapter(settings.FNS_REQUEST_INTERFACE)
    session.mount('http://', interface)
    session.mount('https://', interface)

    response = session.post(
        settings.FNS_URL_ENDPOINT,
        headers=headers,
        params=params,
        data=xml_body
    )

    response.raise_for_status()
    return response


def get_fns_token(fns_response):
    soup = BeautifulSoup(fns_response.text, 'xml')

    token = soup.find('Token')
    expired_at = soup.find('ExpireTime')

    if not all([token, expired_at]):
        raise FnsError

    return token.text, expired_at.text


class Command(BaseCommand):
    def handle(self, *args, **options):
        fns_response = get_fns_response(XML_GET_TOKEN_BODY)
        fns_token, expired_at = get_fns_token(fns_response)

        print(f'Token: {fns_token}')
        print(f'Expired at: {expired_at}')

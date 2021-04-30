import requests

HOST = 'irkkt-mobile.nalog.ru:8888'
DEVICE_OS = 'iOS'
CLIENT_VERSION = '2.9.0'
DEVICE_ID = '7C82010F-16CC-446B-8F66-FC4080C66521'
ACCEPT = '*/*'
USER_AGENT = 'billchecker/2.9.0 (iPhone; iOS 13.6; Scale/2.00)'
ACCEPT_LANGUAGE = 'ru-RU;q=1, en-US;q=0.9'


def get_session_id(inn, client_secret, password):

    url = f'https://{HOST}/v2/mobile/users/lkfl/auth'
    payload = {
        'inn': inn,
        'client_secret': client_secret,
        'password': password
    }
    headers = {
        'Host': HOST,
        'Accept': ACCEPT,
        'Device-OS': DEVICE_OS,
        'Device-Id': DEVICE_ID,
        'clientVersion': CLIENT_VERSION,
        'Accept-Language': ACCEPT_LANGUAGE,
        'User-Agent': USER_AGENT,
    }

    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()['sessionId']


def get_bill_check_id(session_id, qr):
    url = f'https://{HOST}/v2/ticket'
    payload = {'qr': qr}
    headers = {
        'Host': HOST,
        'Accept': ACCEPT,
        'Device-OS': DEVICE_OS,
        'Device-Id': DEVICE_ID,
        'clientVersion': CLIENT_VERSION,
        'Accept-Language': ACCEPT_LANGUAGE,
        'sessionId': session_id,
        'User-Agent': USER_AGENT,
    }
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()["id"]


def get_bill_check_info(bill_check_id, session_id):
    url = f'https://{HOST}/v2/tickets/{bill_check_id}'
    headers = {
        'Host': HOST,
        'Accept': ACCEPT,
        'Device-OS': DEVICE_OS,
        'Device-Id': DEVICE_ID,
        'sessionId': session_id,
        'clientVersion': CLIENT_VERSION,
        'User-Agent': USER_AGENT,
        'Accept-Language': ACCEPT_LANGUAGE,
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()
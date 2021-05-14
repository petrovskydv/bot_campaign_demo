import os
import json
import glob

from dbr import (
    BarcodeReader,
    BarcodeReaderError
)

from environs import Env

GROUPS_OF_SETTING = {
    'Best Coverage Settings': '1',
    'Best Speed Settings': '2',
    'Balance Settings': '3',
    'Super Best Coverage Settings': '4'
}

BARCODE_FORMAT = {
    'All': '1', 'OneD': '2', 'QR Code': '3', 'Code 39': '4',
    'Code 128': '5', 'Code 93': '6', 'Codabar': '7', 'Interleaved 2 of 5': '8',
    'Industrial 2 of 5': '9', 'EAN-13': '10', 'EAN-8': '11', 'UPC-A': '12',
    'UPC-E': '13', 'PDF417': '14', 'DATAMATRIX': '15', 'AZTEC': '16',
    'Code 39 Extended': '17', 'Maxicode': '18', 'GS1 Databar': '19', 'PatchCode': '20',
    'GS1 Composite': '21', 'Postal  Code': '22', 'DotCode': '23'
}

settings_path = 'qr_codes_recognition'


def get_barcode_settings(recognition_quality):
    with open(os.path.join(settings_path, 'qrcode_settings.json'), 'r') as file_handler:
        settings = json.load(file_handler)
        return settings[GROUPS_OF_SETTING[recognition_quality]]


def get_barcode_format(barcode_format):
    with open(os.path.join(settings_path, 'barcode_format.json'), 'r') as file_handler:
        formats = json.load(file_handler)
        return formats[BARCODE_FORMAT[barcode_format]]


def init_runtime_settings(reader, recognition_quality):
    barcode_settings = get_barcode_settings(recognition_quality)
    if barcode_settings:
        reader.init_runtime_settings_with_string(barcode_settings)


def set_barcode_format(reader, barcode_format):
    barcode_format_ids = get_barcode_format(barcode_format)
    if barcode_format:
        settings = reader.get_runtime_settings()
        settings.barcode_format_ids, \
            settings.barcode_format_ids_2 = barcode_format_ids
        reader.update_runtime_settings(settings)


def decode_file(reader, image_file):
    qr_codes = set()
    try:

        text_results = reader.decode_file(image_file)
        if text_results:
            for text_result in text_results:
                qr_codes.add(text_result.barcode_text)

        return qr_codes

    except BarcodeReaderError as error:
        print(error)


def decode_file_stream(reader, image):
    qr_codes = set()
    try:

        text_results = reader.decode_file_stream(bytearray(image))
        if text_results:
            for text_result in text_results:
                qr_codes.add(text_result.barcode_text)

        return qr_codes

    except BarcodeReaderError as error:
        print(error)


def main():
    global settings_path

    env = Env()
    env.read_env()

    settings_path = ''

    license_key = env.str('DYNAM_LICENSE_KEY', '')

    reader = BarcodeReader()
    reader.init_license(license_key)

    init_runtime_settings(reader, 'Super Best Coverage Settings')
    set_barcode_format(reader, 'QR Code')

    images = []
    for file_type in ['jpg', 'jpeg', 'png']:
        images.extend(glob.glob(f'images/*.{file_type}'))

    for image in images:
        qr_codes = decode_file(reader, image)
        print(f'{image}: {qr_codes}')


if __name__ == '__main__':
    main()

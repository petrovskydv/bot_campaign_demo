# Generated by Django 3.2.2 on 2021-05-20 17:34
import os
import json
from django.db import migrations


GROUPS_OF_SETTING = {
    'Best Coverage Settings': '1',
    'Best Speed Settings': '2',
    'Balance Settings': '3',
    'Super Best Coverage Settings': '4'
}


def get_barcode_options():
    all_options = []
    settings_path = 'qr_codes_recognition'
    with open(os.path.join(settings_path, 'qrcode_settings.json'), 'r') as file_handler:
        all_settings_options = json.load(file_handler)
        for key in GROUPS_OF_SETTING.keys():
            options = all_settings_options.get(GROUPS_OF_SETTING[key])
            all_options.append({key: options})
    return all_options


def fill_qr_recognized_settings(apps, schema_editor):
    barcode_options = get_barcode_options()
    if barcode_options:
        Users = apps.get_model('draw_app', 'User')
        for user in Users.objects.all():
            user.qr_setting = barcode_options
            user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('draw_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fill_qr_recognized_settings),
    ]
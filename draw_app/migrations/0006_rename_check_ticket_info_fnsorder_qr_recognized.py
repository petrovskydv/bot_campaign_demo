# Generated by Django 3.2.2 on 2021-05-31 14:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('draw_app', '0005_auto_20210529_1848'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fnsorder',
            old_name='check_ticket_info',
            new_name='qr_recognized',
        ),
    ]

# Generated by Django 3.2.2 on 2021-05-14 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('draw_app', '0002_alter_fnsorder_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fnsorder',
            name='qr_recognized',
        ),
        migrations.AddField(
            model_name='fnsorder',
            name='сheck_ticket_info',
            field=models.CharField(blank=True, db_index=True, max_length=128, verbose_name='Распознанный qr'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='qr_recognized',
            field=models.CharField(blank=True, db_index=True, max_length=128, verbose_name='Распознанный qr'),
        ),
    ]
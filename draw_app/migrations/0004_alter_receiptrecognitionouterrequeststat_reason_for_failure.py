# Generated by Django 3.2.2 on 2021-05-26 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('draw_app', '0003_auto_20210527_0156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiptrecognitionouterrequeststat',
            name='reason_for_failure',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='Причина неудачи'),
        ),
    ]
# Generated by Django 3.2.2 on 2021-05-29 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('draw_app', '0004_alter_receiptrecognitionouterrequeststat_reason_for_failure'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='receiptrecognitionouterrequeststat',
            options={'ordering': ['-start_time'], 'verbose_name': 'Статистика распознавания (qr коды и ФНС)'},
        ),
        migrations.AlterField(
            model_name='customer',
            name='quality_setting',
            field=models.CharField(choices=[('Best Coverage Settings', 'Высокое качество распознавания'), ('Best Speed Settings', 'Высокая скорость распознавания'), ('Balance Settings', 'Сбалансированные настройки'), ('Ultimate Coverage Settings', 'Максимальное качество распознавания')], db_index=True, default='Ultimate Coverage Settings', max_length=30, verbose_name='Настройка качества распознавания qr-кодов'),
        ),
        migrations.AlterField(
            model_name='receiptrecognitionouterrequeststat',
            name='dynamsoft_quality_setting',
            field=models.CharField(blank=True, db_index=True, max_length=30, verbose_name='Настройка качества распознавания qr-кодов'),
        ),
    ]

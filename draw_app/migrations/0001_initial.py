# Generated by Django 3.2.2 on 2021-05-20 17:34

import django.contrib.auth.models
import django.contrib.auth.validators
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_joined', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Когда присоединился')),
                ('tg_username', models.CharField(blank=True, default='', max_length=64, verbose_name='Юзернейм в Telegram')),
                ('tg_first_name', models.CharField(blank=True, default='', max_length=64, verbose_name='Имя в Telegram')),
                ('tg_chat_id', models.PositiveIntegerField(db_index=True, unique=True, verbose_name='Telegram chat ID')),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, db_index=True, max_length=128, null=True, region=None, verbose_name='Телефон')),
            ],
            options={
                'verbose_name': 'Участник',
                'verbose_name_plural': 'Участники',
                'ordering': ['-date_joined'],
            },
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Когда загружен')),
                ('image', models.ImageField(upload_to='receipts', verbose_name='Фото чека')),
                ('qr_recognized', models.CharField(blank=True, db_index=True, default='', max_length=128, verbose_name='Распознанный qr')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='receipts', to='draw_app.customer', verbose_name='Участник')),
            ],
            options={
                'verbose_name': 'Чек',
                'verbose_name_plural': 'Чеки',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='QRCodeRecognitionAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_to', models.CharField(choices=[('dynamsoft', 'чтение qr-кодов'), ('fns_api', 'получение данных из ФНС')], db_index=True, max_length=25, verbose_name='Наименование сервиса для анализа чека')),
                ('start_time', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Время отправки чека для анализа')),
                ('end_time', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Время получения ответа')),
                ('reason_for_failure', models.CharField(blank=True, db_index=True, default='', max_length=255, verbose_name='Причина неудачи анализа чека')),
                ('receipt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='draw_app.receipt', verbose_name='Чек')),
            ],
            options={
                'verbose_name': 'Статистика распознования чеков',
                'ordering': ['-start_time'],
            },
        ),
        migrations.CreateModel(
            name='FnsOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_requested_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Время первого запроса')),
                ('last_requested_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Время последнего запроса')),
                ('check_ticket_info', models.CharField(blank=True, db_index=True, default='', max_length=128, verbose_name='Распознанный qr')),
                ('status', models.CharField(choices=[('raw', 'не обработан'), ('sent', 'отправлен'), ('received', 'получен'), ('closed', 'закрыт')], db_index=True, default='raw', max_length=25, verbose_name='Статус')),
                ('answer', models.JSONField(db_index=True, default=dict, verbose_name='Ответ налоговой')),
                ('receipt', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fns_orders', to='draw_app.receipt', verbose_name='Чек')),
            ],
            options={
                'verbose_name': 'Запрос к ФНС',
                'verbose_name_plural': 'Запросы к ФНС',
                'ordering': ['-last_requested_at'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('qr_setting', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(blank=True, null=True), blank=True, null=True, size=None, verbose_name='Вариант настройки чтения qr кодов')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]

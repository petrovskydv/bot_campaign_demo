from django.db import models
from django.utils.html import mark_safe
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator


class Customer(models.Model):

    GROUPS_OF_SETTING = (
        ('Best Coverage Settings', 'Высокое качество распознавания'),
        ('Best Speed Settings', 'Высокая скорость распознавания'),
        ('Balance Settings', 'Сбалансированные настройки'),
        ('Ultimate Coverage Settings', 'Максимальное качество распознавания'),
    )

    date_joined = models.DateTimeField(
        'Когда присоединился',
        auto_now_add=True,
        db_index=True
    )
    tg_username = models.CharField(
        'Юзернейм в Telegram',
        max_length=64,
        blank=True,
    )
    tg_first_name = models.CharField(
        'Имя в Telegram',
        max_length=64,
        blank=True,
    )
    tg_chat_id = models.PositiveIntegerField(
        'Telegram chat ID',
        db_index=True,
        unique=True
    )
    phone = PhoneNumberField(
        'Телефон',
        blank=True,
        null=True,
        db_index=True
    )
    quality_setting = models.CharField(
        verbose_name='Настройка качества распознования qr-кодов',
        choices=GROUPS_OF_SETTING,
        default='Ultimate Coverage Settings',
        max_length=30,
        db_index=True
    )

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def __str__(self):
        return self.tg_username


class Receipt(models.Model):
    uploaded_at = models.DateTimeField(
        'Когда загружен',
        auto_now_add=True,
        db_index=True
    )
    image = models.ImageField(
        'Фото чека',
        upload_to='receipts'
    )
    customer = models.ForeignKey(
        Customer,
        verbose_name='Участник',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='receipts'
    )
    qr_recognized = models.CharField(
        'Распознанный qr',
        max_length=128,
        blank=True,
        db_index=True,
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Чек'
        verbose_name_plural = 'Чеки'

    def __str__(self):
        return f'{self.uploaded_at}'

    def get_preview(self):
        return mark_safe(f'<img src="{self.image.url}" width="300">')


class FnsOrderQuerySet(models.QuerySet):
    def raw(self):
        return self.filter(status='raw')


class FnsOrder(models.Model):

    TYPES_OF_STATUS = (
        ('raw', 'не обработан'),
        ('sent', 'отправлен'),
        ('received', 'получен'),
        ('closed', 'закрыт'),
    )

    receipt = models.ForeignKey(
        Receipt,
        verbose_name='Чек',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='fns_orders'
    )
    first_requested_at = models.DateTimeField(
        'Время первого запроса',
        auto_now_add=True,
        db_index=True
    )
    last_requested_at = models.DateTimeField(
        'Время последнего запроса',
        auto_now=True,
        db_index=True
    )
    check_ticket_info = models.CharField(
        'Распознанный qr',
        max_length=128,
        blank=True,
        db_index=True,
    )
    status = models.CharField(
        verbose_name='Статус',
        choices=TYPES_OF_STATUS,
        max_length=25,
        default='raw',
        db_index=True,
    )
    answer = models.JSONField(
        'Ответ налоговой',
        default=dict,
        db_index=True
    )

    objects = FnsOrderQuerySet.as_manager()

    class Meta:
        ordering = ['-last_requested_at']
        verbose_name = 'Запрос к ФНС'
        verbose_name_plural = 'Запросы к ФНС'

    def __str__(self):
        return f'{self.first_requested_at}'


class ReceiptRecognitionOuterRequestStatQuerySet(models.QuerySet):
    def get_successful_attempts(self, request_to, receipt_id):
        return self.filter(
            receipt__id=receipt_id, request_to=request_to, reason_for_failure=''
        ).order_by('-start_time')

    def get_failed_attempts(self, request_to, receipt_id):
        return self.filter(
            receipt__id=receipt_id, request_to=request_to
        ).exclude(reason_for_failure='').order_by('-start_time', 'sent_notification')


class ReceiptRecognitionOuterRequestStat(models.Model):

    TYPES_OF_REQUESTS = (
        ('dynamsoft', 'чтение qr-кодов'),
        ('fns_api', 'получение данных из ФНС'),
    )

    request_to = models.CharField(
        'Сервис для анализа чека',
        choices=TYPES_OF_REQUESTS,
        max_length=25,
        db_index=True,
    )
    start_time = models.DateTimeField(
        'Время отправки чека',
        auto_now_add=True,
        db_index=True
    )
    end_time = models.DateTimeField(
        'Время получения ответа',
        auto_now_add=True,
        db_index=True
    )
    reason_for_failure = models.CharField(
        'Причина неудачи',
        max_length=255,
        blank=True,
        db_index=True
    )
    dynamsoft_quality_setting = models.CharField(
        'Настройка качества распознования qr-кодов',
        blank=True,
        max_length=30,
        db_index=True
    )
    receipt = models.ForeignKey(
        Receipt,
        verbose_name='Чек',
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    sent_notification = models.BooleanField(default=False)

    objects = ReceiptRecognitionOuterRequestStatQuerySet.as_manager()

    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Статистика распознования (qr коды и ФНС)'

    def __str__(self):
        return f'{self.request_to} {self.start_time}'

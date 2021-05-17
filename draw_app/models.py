from django.db import models
from django.utils.html import format_html
from phonenumber_field.modelfields import PhoneNumberField


TYPES_OF_STATUS = (
    ('raw', 'не обработан'),
    ('sent', 'отправлен'),
    ('received', 'получен'),
    ('closed', 'закрыт'),
)


class Customer(models.Model):
    date_joined = models.DateTimeField(
        'Когда присоединился',
        auto_now_add=True,
        db_index=True
    )
    tg_username = models.CharField(
        'Юзернейм в Telegram',
        max_length=64,
        blank=True,
        default=''
    )
    tg_first_name = models.CharField(
        'Имя в Telegram',
        max_length=64,
        blank=True,
        default=''
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
        default='',
        db_index=True
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Чек'
        verbose_name_plural = 'Чеки'

    def __str__(self):
        return f'{self.uploaded_at}'

    def get_preview(self):
        return format_html(f'<img src="{self.image.url}" width="300">')


class FnsOrderQuerySet(models.QuerySet):
    def raw(self):
        return self.filter(status='raw')


class FnsOrder(models.Model):

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
    сheck_ticket_info = models.CharField(
        'Распознанный qr',
        max_length=128,
        blank=True,
        default='',
        db_index=True
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

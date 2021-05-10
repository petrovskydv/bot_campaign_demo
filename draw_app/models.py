from django.db import models
from django.utils.html import format_html
from phonenumber_field.modelfields import PhoneNumberField


class Customer(models.Model):
    created_at = models.DateTimeField('Зарегистрирован', auto_now_add=True)
    username = models.CharField('Юзернейм', max_length=64, blank=True, null=True)
    first_name = models.CharField('Имя', max_length=64, blank=True, null=True)
    telegram_chat_id = models.PositiveIntegerField('Telegram chat ID')
    phone = PhoneNumberField('Телефон', blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'


class Receipt(models.Model):
    uploaded_at = models.DateTimeField('Загружен', auto_now_add=True)
    image = models.ImageField('Фото чека', upload_to='receipts')
    customer = models.ForeignKey(Customer, verbose_name='Участник', on_delete=models.PROTECT, related_name='receipts')

    def __str__(self):
        return f'{self.uploaded_at}'

    def get_preview(self):
        return format_html(f'<img src="{self.image.url}" width="300">')

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Чек'
        verbose_name_plural = 'Чеки'


class FnsOrder(models.Model):
    SENT = 1
    RECEIVED = 2
    NOT_RECEIVED = 3
    EXPIRED = 4

    STATUS_CHOICES = [
        [SENT, 'Запрос отправлен'],
        [RECEIVED, 'Ответ получен'],
        [NOT_RECEIVED, 'Ответа еще нет'],
        [EXPIRED, 'Истек срок'],
    ]

    receipt = models.ForeignKey(Receipt, verbose_name='Чек', on_delete=models.PROTECT, related_name='fns_orders')
    first_request_at = models.DateTimeField('Время первого запроса', auto_now_add=True)
    last_request_at = models.DateTimeField('Время последнего запроса', auto_now=True)
    qr_recognized = models.CharField('Распознанный qr', max_length=128)
    status = models.PositiveSmallIntegerField('Статус', choices=STATUS_CHOICES, default=SENT)
    answer = models.JSONField('Ответ налоговой', default=dict, blank=True)

    def __str__(self):
        return f'{self.first_request_at}'

    class Meta:
        ordering = ['-last_request_at']
        verbose_name = 'Запрос к ФНС'
        verbose_name_plural = 'Запросы к ФНС'

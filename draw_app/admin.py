from django.contrib import admin
from django.utils.safestring import mark_safe


from .models import (
    User,
    Customer,
    FnsOrder,
    Receipt,
    QRCodeRecognitionAttempt
)


class ReceiptInline(admin.TabularInline):
    model = Receipt
    readonly_fields = ['get_preview']
    extra = 1


class FnsInline(admin.TabularInline):
    model = FnsOrder
    extra = 1
    can_delete = False
    readonly_fields = ['answer']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    inlines = [ReceiptInline]
    list_display = [
        'date_joined',
        'tg_username',
        'tg_first_name',
        'tg_chat_id',
        'phone',
    ]
    list_filter = ['date_joined']
    search_fields = ['date_joined', 'tg_chat_id', 'phone']


@admin.register(FnsOrder)
class FnsOrderAdmin(admin.ModelAdmin):
    list_display = [
        'receipt',
        'first_requested_at',
        'last_requested_at',
        'check_ticket_info',
        'status',
    ]
    list_filter = ['first_requested_at', 'last_requested_at']
    readonly_fields = ['answer']


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    inlines = [FnsInline]
    list_display = ['uploaded_at', 'customer']
    list_filter = ['uploaded_at']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(QRCodeRecognitionAttempt)
class QRCodeRecognitionAttemptAdmin(admin.ModelAdmin):
    readonly_fields = ['preview_field']
    list_display = [
        'receipt',
        'request_to',
        'start_time',
        'end_time',
        'recognition_time_field',
        'reason_for_failure',
        'preview_field',
    ]
    list_filter = ['request_to', 'start_time', 'end_time', 'reason_for_failure']

    def preview_field(self, instance):
        return mark_safe(f'<img src="{instance.receipt.image.url}" height=100px>')

    def recognition_time_field(self, instance):
        recognition_time = (instance.end_time - instance.start_time)
        return mark_safe(f'<p>{recognition_time.seconds}.{recognition_time.microseconds}</p>')

    preview_field.short_description = u'превью чека'
    recognition_time_field.short_description = u'время распознования, сек'

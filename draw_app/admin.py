from django.contrib import admin

from .models import (
    Customer,
    FnsOrder,
    Receipt
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
        'created_at',
        'username',
        'first_name',
        'telegram_chat_id',
        'phone',
    ]
    list_filter = ['created_at']
    search_fields = ['username', 'first_name', 'telegram_chat_id', 'phone']


@admin.register(FnsOrder)
class FnsOrderAdmin(admin.ModelAdmin):
    list_display = [
        'receipt',
        'first_request_at',
        'last_request_at',
        'qr_recognized',
        'status',
    ]
    list_filter = ['first_request_at', 'last_request_at']
    readonly_fields = ['answer']


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    inlines = [FnsInline]
    list_display = ['uploaded_at', 'customer']
    list_filter = ['uploaded_at']

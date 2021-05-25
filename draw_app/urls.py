from django.urls import path

from .views import handle_receipt_image, handle_purchases


app_name = 'draw_app'

urlpatterns = [
    path('send_image/', handle_receipt_image),
    path('purchases/<int:tg_chat_id>/', handle_purchases),
]

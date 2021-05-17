from django.urls import path

from .views import handle_receipt_image


app_name = 'draw_app'

urlpatterns = [
    path('send_image/', handle_receipt_image),
]

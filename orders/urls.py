# duzanda/orders/urls.py

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('my/', views.my_orders, name='my_orders'),
]

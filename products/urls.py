from django.urls import path
from . import views
from . import views_debug

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_add, name='product_add'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Диагностические URL (только для администраторов)
    path('debug/check-s3-images/', views_debug.check_s3_images, name='check_s3_images'),
    path('debug/test-s3-images/', views_debug.test_s3_images, name='test_s3_images'),
]

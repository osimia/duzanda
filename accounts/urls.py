from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('update-profile-ajax/', views.update_profile_ajax, name='update_profile_ajax'),  # Новый URL для AJAX
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my-products/', views.my_products, name='my_products'),
    path('master-register/', views.master_register_entry, name='master_register'),
    path('master-login/', views.master_login_entry, name='master_login'),
]

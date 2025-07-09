# duzanda/views.py
from django.shortcuts import render, redirect

from products.models import Product, Category

def master_landing(request):
    """Landing page for master URL path, providing login and registration options"""
    # Determine if user is already authenticated
    if request.user.is_authenticated:
        # Если пользователь уже авторизован, перенаправляем на домашнюю страницу
        # Для мастеров можно было бы сделать перенаправление на специальную панель мастера
        return redirect('home')
    
    # Эта страница доступна только для мастеров, так как находится по специальному URL /master/
    return render(request, 'master_landing.html')

def home(request):
    products = Product.objects.order_by('-created_at')[:8]
    return render(request, 'home.html', {'products': products})


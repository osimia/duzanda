# duzanda/orders/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.utils.crypto import get_random_string
from cart.models import CartItem
from cart.views import get_cart_owner_info
from accounts.models import User
from .models import Order, OrderItem
import re

def checkout(request):
    # Получаем корзину на основе авторизации или сессии
    owner_filter, _ = get_cart_owner_info(request)
    cart_items = CartItem.objects.filter(**owner_filter)
    
    if not cart_items.exists():
        messages.info(request, "Ваша корзина пуста.")
        return redirect('products:product_list')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        delivery_address = request.POST.get('delivery_address')
        
        # Базовая валидация
        if not phone or not delivery_address:
            messages.error(request, "Пожалуйста, заполните все обязательные поля.")
            return redirect('orders:checkout')
            
        # Очистка номера телефона от нецифровых символов
        clean_phone = re.sub(r'\D', '', phone)
        if len(clean_phone) < 10:
            messages.error(request, "Пожалуйста, введите корректный номер телефона (минимум 10 цифр).")
            return redirect('orders:checkout')
            
        user = request.user
        
        # Если пользователь не авторизован, создаем новый аккаунт или находим существующий
        if not request.user.is_authenticated:
            # Ищем пользователя с таким телефоном
            existing_user = User.objects.filter(phone=clean_phone).first()
            
            if existing_user:
                user = existing_user
                # Если нашли пользователя, авторизуем его
                login(request, user)
                messages.success(request, f"Вход выполнен по номеру телефона {phone}.")
            else:
                # Создаем нового пользователя
                username = f"user_{get_random_string(8)}"
                password = get_random_string(12)
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    phone=clean_phone,
                    role='buyer'
                )
                login(request, user)
                messages.success(request, f"Аккаунт создан автоматически. Ваш логин: {username}. Пароль отправлен на ваш номер телефона.")
                
            # Перенос товаров из анонимной корзины в корзину пользователя
            if 'session_key' in owner_filter:
                session_cart_items = CartItem.objects.filter(session_key=request.session.session_key)
                for item in session_cart_items:
                    item.buyer = user
                    item.session_key = None
                    item.save()
        
        total_amount = sum(item.product.price * item.quantity for item in cart_items)

        # Создаем заказ
        order = Order.objects.create(
            buyer=user,
            phone_number=clean_phone,
            delivery_address=delivery_address,
            total_amount=total_amount
        )

        # Добавляем товары в заказ
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            
        # Очищаем корзину
        cart_items.delete()
        
        # Разные сообщения для новых и существующих пользователей
        if not request.user.is_authenticated or not hasattr(request.user, 'last_login') or request.user.last_login is None:
            messages.success(request, f"Заказ #{order.id} успешно оформлен! Добро пожаловать в личный кабинет, где вы можете отслеживать статус своих заказов.")
        else:
            messages.success(request, f"Заказ #{order.id} успешно оформлен! Вы можете отслеживать статус заказа в своем профиле.")
        
        return redirect('accounts:profile')

    # Подсчитываем общую сумму
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })


def my_orders(request):
    # Если пользователь авторизован, показываем его заказы
    if request.user.is_authenticated:
        orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
        return render(request, 'orders/my_orders.html', {'orders': orders})
    
    # Для неавторизованных пользователей
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if phone:
            # Очистка номера телефона от нецифровых символов
            clean_phone = re.sub(r'\D', '', phone)
            if len(clean_phone) >= 10:
                orders = Order.objects.filter(phone_number=clean_phone).order_by('-created_at')
                if orders:
                    return render(request, 'orders/my_orders.html', {
                        'orders': orders,
                        'guest_phone': phone
                    })
                else:
                    messages.error(request, "По указанному номеру телефона заказов не найдено.")
            else:
                messages.error(request, "Пожалуйста, введите корректный номер телефона.")
    
    # По умолчанию показываем форму для ввода телефона
    return render(request, 'orders/find_orders.html')


def find_orders(request):
    """
    Отдельная страница для поиска заказов по номеру телефона.
    Позволяет неавторизованным пользователям найти свои заказы.
    """
    orders = None
    phone = None
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if phone:
            # Очистка номера телефона от нецифровых символов
            clean_phone = re.sub(r'\D', '', phone)
            if len(clean_phone) >= 10:
                orders = Order.objects.filter(phone_number=clean_phone).order_by('-created_at')
                if not orders:
                    messages.error(request, "По указанному номеру телефона заказов не найдено.")
            else:
                messages.error(request, "Пожалуйста, введите корректный номер телефона.")
    
    return render(request, 'orders/find_orders.html', {
        'orders': orders,
        'phone': phone
    })

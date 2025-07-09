from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import re
import json

from .forms import UserRegisterForm, UserUpdateForm, UserLoginForm, PhoneLoginForm
from .models import User
from products.models import Product

def register(request):
    # Check if registration is for a master (should only be accessible via /master URL)
    is_master = request.session.get('is_master_registration', False)
    if not is_master:
        # Если это не регистрация мастера, перенаправляем на логин (вход по телефону)
        messages.error(request, 'Регистрация доступна только для мастеров через специальную ссылку.')
        return redirect('accounts:login')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Clear the session flag
            if 'is_master_registration' in request.session:
                del request.session['is_master_registration']
            return redirect('home')
    else:
        # For master registration, pre-select 'master' role
        form = UserRegisterForm(initial={'role': 'master'})
    return render(request, 'accounts/register.html', {'form': form, 'is_master': True})

def master_register_entry(request):
    # Set a session flag to indicate this is a master registration
    request.session['is_master_registration'] = True
    
    # Clear any existing messages
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # This consumes the messages
    
    # Add a message for masters
    messages.info(request, 'Регистрация нового мастера. Пожалуйста, заполните форму.')
    
    # Redirect to the standard registration page
    return redirect('accounts:register')

def profile(request):
    # Для неавторизованных пользователей показываем упрощенный профиль
    if not request.user.is_authenticated:
        return render(request, 'accounts/guest_profile.html')
    
    # Для авторизованных пользователей
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    # Check if this is a master login access
    is_master = request.session.get('is_master_login', False)
    
    # Для мастеров всегда вход по логину/паролю, для обычных пользователей - только по телефону
    login_type = 'username' if is_master else 'phone'
    
    if request.method == 'POST':
        if login_type == 'phone':
            # Вход по номеру телефона
            form = PhoneLoginForm(request.POST)
            if form.is_valid():
                phone = form.cleaned_data['phone']
                # Очистка номера телефона от нецифровых символов
                clean_phone = re.sub(r'\D', '', phone)
                
                if len(clean_phone) < 10:
                    messages.error(request, "Пожалуйста, введите корректный номер телефона (минимум 10 цифр).")
                else:
                    # Поиск пользователя с таким номером телефона
                    user = User.objects.filter(phone=clean_phone).first()
                    
                    if user:
                        # Если пользователь найден, авторизуем его
                        login(request, user)
                        messages.success(request, f"Вход выполнен по номеру телефона {phone}.")
                        return redirect('accounts:profile')
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
                        messages.success(request, f"Аккаунт создан автоматически с номером телефона {phone}. Ваш логин: {username}")
                        return redirect('accounts:profile')
        else:
            # Стандартный вход по логину и паролю
            form = UserLoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
                
                if user:
                    # If this is master login path, check if user is a master
                    if is_master and (not hasattr(user, 'role') or user.role != 'master'):
                        messages.error(request, 'Этот вход только для мастеров.')
                    else:
                        login(request, user)
                        # Clear the session flag
                        if 'is_master_login' in request.session:
                            del request.session['is_master_login']
                        return redirect('accounts:profile')
                else:
                    messages.error(request, 'Неверный логин или пароль.')
    else:
        # Создаем соответствующую форму в зависимости от типа входа
        if login_type == 'phone':
            form = PhoneLoginForm()
        else:
            form = UserLoginForm()
    
    # Pass is_master to template along with login_type
    return render(request, 'accounts/login.html', {
        'form': form, 
        'is_master': is_master,
        'login_type': login_type
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def my_products(request):
    if not hasattr(request.user, 'role') or request.user.role != 'master':
        return redirect('accounts:profile')
    products = Product.objects.filter(master=request.user)
    return render(request, 'accounts/my_products.html', {'products': products})

def master_login_entry(request):
    # Set a session flag to indicate this is a master login
    request.session['is_master_login'] = True
    
    # Clear any existing messages
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # This consumes the messages
    
    # Add a message for masters
    messages.info(request, 'Вход для мастеров. Пожалуйста, введите свои данные.')
    
    # Redirect to the standard login page
    return redirect('accounts:login')

@login_required
@require_POST
def update_profile_ajax(request):
    """Обрабатывает AJAX-запрос для обновления профиля пользователя."""
    form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
    
    if form.is_valid():
        form.save()
        # Формируем ответ с обновленными данными
        response_data = {
            'success': True,
            'message': 'Профиль успешно обновлён!',
            'user': {
                'username': request.user.username,
                'email': request.user.email or 'Не указан',
                'phone': request.user.phone or 'Не указан',
                'address': request.user.address or 'Не указан',
                # Если у пользователя есть аватар, возвращаем URL, иначе None
                'avatar_url': request.user.avatar.url if request.user.avatar else None,
                'avatar_initial': request.user.username[0].upper() if request.user.username else '',
            }
        }
        return JsonResponse(response_data)
    else:
        # Если есть ошибки в форме, возвращаем их
        return JsonResponse({
            'success': False, 
            'errors': form.errors.as_json()
        }, status=400)

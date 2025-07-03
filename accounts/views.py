from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import UserRegisterForm, UserUpdateForm, UserLoginForm
from products.models import Product

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
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

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Неверный логин или пароль.')
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

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

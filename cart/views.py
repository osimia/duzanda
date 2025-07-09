# duzanda/cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import CartItem
from products.models import Product

def get_cart_owner_info(request):
    """Получает информацию о владельце корзины (пользователь или сессия)"""
    if request.user.is_authenticated:
        return {'buyer': request.user}, {'buyer': request.user}
    else:
        # Убедимся, что у нас есть ключ сессии
        if not request.session.session_key:
            request.session.create()
        return {'session_key': request.session.session_key}, {'session_key': request.session.session_key}

def view_cart(request):
    owner_filter, _ = get_cart_owner_info(request)
    
    cart_items = CartItem.objects.filter(**owner_filter)
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render(request, 'cart/cart_view.html', {
        'cart_items': cart_items,
        'total': total,
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get('size', '')
    quantity = int(request.POST.get('quantity', 1))
    
    # Проверяем корректность размера, если размеры указаны для товара
    valid_sizes = [s.strip() for s in product.sizes.split(',') if s.strip()]
    if product.sizes and size not in valid_sizes:
        messages.error(request, 'Пожалуйста, выберите корректный размер.')
        return redirect('products:product_detail', pk=product_id)
    
    owner_filter, owner_data = get_cart_owner_info(request)
    
    # Проверяем, есть ли уже такой товар в корзине
    existing_item = CartItem.objects.filter(product=product, size=size, **owner_filter).first()
    
    if existing_item:
        existing_item.quantity += quantity
        existing_item.save()
        messages.success(request, f"Количество товара {product.name} обновлено в корзине.")
    else:
        CartItem.objects.create(
            product=product,
            quantity=quantity,
            size=size,
            **owner_data
        )
        messages.success(request, f"Товар {product.name} добавлен в корзину.")
    
    return redirect('products:product_detail', pk=product_id)

def remove_from_cart(request, pk):
    owner_filter, _ = get_cart_owner_info(request)
    item = get_object_or_404(CartItem, pk=pk, **owner_filter)
    item.delete()
    messages.success(request, "Товар удален из корзины.")
    return redirect('cart:view_cart')

def update_quantity(request, pk, action):
    owner_filter, _ = get_cart_owner_info(request)
    item = get_object_or_404(CartItem, pk=pk, **owner_filter)
    
    if action == 'increase':
        item.quantity += 1
        messages.success(request, "Количество товара увеличено.")
    elif action == 'decrease' and item.quantity > 1:
        item.quantity -= 1
        messages.success(request, "Количество товара уменьшено.")
    
    item.save()
    return redirect('cart:view_cart')

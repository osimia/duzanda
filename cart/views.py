# duzanda/cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CartItem
from products.models import Product

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(buyer=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart/cart_view.html', {
        'cart_items': cart_items,
        'total': total,
    })

@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, buyer=request.user)
    item.delete()
    return redirect('cart:view_cart')

@login_required
def update_quantity(request, pk, action):
    item = get_object_or_404(CartItem, pk=pk, buyer=request.user)
    if action == 'increase':
        item.quantity += 1
    elif action == 'decrease' and item.quantity > 1:
        item.quantity -= 1
    item.save()
    return redirect('cart:view_cart')

# duzanda/orders/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cart.models import CartItem
from .models import Order, OrderItem

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(buyer=request.user)
    if not cart_items.exists():
        messages.info(request, "Ваша корзина пуста.")
        return redirect('products:product_list')

    if request.method == 'POST':
        delivery_address = request.POST.get('delivery_address')
        if not delivery_address:
            messages.error(request, "Пожалуйста, укажите адрес доставки.")
            return redirect('orders:checkout')

        total_amount = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            buyer=request.user,
            delivery_address=delivery_address,
            total_amount=total_amount
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        cart_items.delete()
        messages.success(request, f"Заказ #{order.id} успешно оформлен!")
        return redirect('products:product_list')

    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items
    })


# duzanda/orders/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Order

@login_required
def my_orders(request):
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {
        'orders': orders
    })

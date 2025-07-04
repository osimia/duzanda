# duzanda/views.py
from django.shortcuts import render

from products.models import Product, Category

def home(request):
    products = Product.objects.order_by('-created_at')[:8]
    categories = Category.objects.all()
    return render(request, 'home.html', {'products': products, 'categories': categories})


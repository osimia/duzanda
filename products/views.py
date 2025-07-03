from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductImage
from cart.models import CartItem
from .forms import ProductForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages

def product_list(request):
    category_id = request.GET.get('category')
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()

    if category_id:
        products = products.filter(category_id=category_id)

    context = {
        'products': products,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart_item, created = CartItem.objects.get_or_create(
        buyer=request.user,
        product=product,
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart:view_cart')

@login_required
def product_add(request):
    if not hasattr(request.user, 'role') or request.user.role != 'master':
        return redirect('products:product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.master = request.user
            product.save()
            # Сохраняем фото
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(product=product, image=image)
            return redirect('products:product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_add.html', {'form': form})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, master=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар успешно обновлён!')
            return redirect('accounts:my_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_add.html', {'form': form, 'edit_mode': True})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, master=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Товар удалён!')
        return redirect('accounts:my_products')
    return redirect('accounts:my_products')

from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductImage
from cart.models import CartItem
from .forms import ProductForm, ProductImageForm, ProductImageFormSet
from django.forms import modelformset_factory

from django.contrib.auth.decorators import login_required
from django.contrib import messages

def product_list(request):
    category_id = request.GET.get('category')
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()

    if category_id:
        products = products.filter(category_id=category_id)

    # Для каждого товара формируем список уникальных размеров
    products_with_sizes = []
    for product in products:
        sizes = [s.strip() for s in product.sizes.split(',') if s.strip()]
        # Удаляем дубликаты, сохраняем порядок
        unique_sizes = []
        for s in sizes:
            if s not in unique_sizes:
                unique_sizes.append(s)
        products_with_sizes.append({
            'product': product,
            'sizes': unique_sizes,
        })
    context = {
        'products_with_sizes': products_with_sizes,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    sizes = [s.strip() for s in product.sizes.split(',') if s.strip()]
    return render(request, 'products/product_detail.html', {'product': product, 'sizes': sizes})

# Функция add_to_cart перемещена в cart/views.py для поддержки анонимных пользователей

@login_required
def product_add(request):
    if not hasattr(request.user, 'role') or request.user.role != 'master':
        return redirect('products:product_list')
    
    # Создаем формсет с меньшим количеством полей для уменьшения нагрузки
    ImageFormSet = modelformset_factory(
        ProductImage,
        form=ProductImageForm,
        extra=3,  # Уменьшаем количество пустых форм
        max_num=5  # Уменьшаем максимальное количество форм для одновременной загрузки
    )
    
    if request.method == 'POST':
        try:
            form = ProductForm(request.POST)
            formset = ImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())
            
            # Проверяем валидность формы продукта отдельно от формсета
            if form.is_valid():
                # Сначала сохраняем продукт
                product = form.save(commit=False)
                product.master = request.user
                product.save()
                
                # Показываем сообщение о сохранении продукта
                messages.success(request, 'Товар успешно создан!')
                
                # Теперь обрабатываем изображения
                if formset.is_valid():
                    # Подсчитываем количество форм с изображениями
                    image_forms_with_data = [f for f in formset if f.cleaned_data and 'image' in f.cleaned_data and f.cleaned_data['image']]
                    total_images = len(image_forms_with_data)
                    
                    if total_images > 0:
                        messages.info(request, f'Загрузка {total_images} изображений. Пожалуйста, подождите...')
                    
                    # Обрабатываем каждую форму в формсете с обработкой ошибок
                    for i, image_form in enumerate(formset):
                        # Пропускаем пустые формы
                        if image_form.cleaned_data and 'image' in image_form.cleaned_data and image_form.cleaned_data['image']:
                            try:
                                # Сохраняем изображение, связывая его с продуктом
                                image_form.save(product=product)
                            except Exception as e:
                                import traceback
                                print(f"Ошибка при сохранении изображения {i+1}: {e}")
                                traceback.print_exc()
                                messages.error(request, f"Не удалось загрузить изображение {i+1}: {str(e)}")
                
                # Даже если загрузка изображений не удалась, продукт всё равно создан
                return redirect('products:product_list')
            else:
                # Ошибки в форме продукта
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Ошибка в поле {field}: {error}")
                
        except Exception as e:
            # Общая обработка непредвиденных ошибок
            import traceback
            print(f"Непредвиденная ошибка при создании товара: {e}")
            traceback.print_exc()
            messages.error(request, f"Произошла ошибка: {str(e)}")
    else:
        form = ProductForm()
        formset = ImageFormSet(queryset=ProductImage.objects.none())
        
    return render(request, 'products/product_add.html', {
        'form': form,
        'formset': formset
    })

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, master=request.user)
    
    # Формируем формсет для существующих изображений продукта
    ImageFormSet = modelformset_factory(
        ProductImage,
        form=ProductImageForm,
        extra=3,
        max_num=10,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        formset = ImageFormSet(
            request.POST, 
            request.FILES,
            queryset=ProductImage.objects.filter(product=product)
        )
        
        if form.is_valid() and formset.is_valid():
            # Сохраняем основную информацию о продукте
            form.save()
            
            # Обрабатываем каждую форму в формсете
            for image_form in formset:
                if image_form.cleaned_data:
                    # Обрабатываем удаление
                    if image_form.cleaned_data.get('DELETE'):
                        if image_form.instance.pk:
                            image_form.instance.delete()
                    elif 'image' in image_form.cleaned_data and image_form.cleaned_data['image']:
                        # Сохраняем новое изображение
                        image_form.save(product=product)
            
            messages.success(request, 'Товар успешно обновлён!')
            return redirect('accounts:my_products')
    else:
        form = ProductForm(instance=product)
        formset = ImageFormSet(queryset=ProductImage.objects.filter(product=product))
        
    return render(request, 'products/product_add.html', {
        'form': form,
        'formset': formset,
        'edit_mode': True,
        'product': product
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, master=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Товар удалён!')
        return redirect('accounts:my_products')
    return redirect('accounts:my_products')

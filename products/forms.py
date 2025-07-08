from django import forms
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Product, ProductImage
from duzanda.storage_backends import ProductImagesStorage
import io
from PIL import Image as PILImage
import threading

class ProductForm(forms.ModelForm):
    sizes = forms.MultipleChoiceField(
        choices=Product.SIZES,
        widget=forms.CheckboxSelectMultiple,
        label='Размеры',
        required=False,
        help_text='Выберите один или несколько размеров',
    )

    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'old_price', 'stock', 'sizes']
        labels = {
            'category': 'Категория',
            'name': 'Название',
            'description': 'Описание',
            'price': 'Цена',
            'old_price': 'Старая цена',
            'stock': 'Количество',
            'sizes': 'Размеры',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # При редактировании товара преобразуем строку в список
        if self.instance and self.instance.sizes:
            self.initial['sizes'] = [s.strip() for s in self.instance.sizes.split(',') if s.strip()]

    def clean_sizes(self):
        sizes = self.cleaned_data.get('sizes', [])
        # Удаляем дубликаты и пустые значения
        unique_sizes = []
        for s in sizes:
            if s and s not in unique_sizes:
                unique_sizes.append(s)
        return ','.join(unique_sizes)

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
    def _optimize_image(self, image_file):
        """
        Оптимизирует изображение для быстрой загрузки на S3
        """
        try:
            # Открываем изображение через PIL
            img = PILImage.open(image_file)
            
            # Проверяем размер и формат
            if img.width > 1200 or img.height > 1200:
                # Сжимаем большие изображения
                img.thumbnail((1200, 1200), PILImage.LANCZOS)
            
            # Оптимизируем и сохраняем в буфер
            output_io = io.BytesIO()
            
            # Конвертируем в WebP для лучшего сжатия
            if img.mode == 'RGBA':
                background = PILImage.new('RGBA', img.size, (255, 255, 255))
                background.paste(img, img.split()[-1])
                img = background
                
            # Сохраняем в оптимизированном формате
            format = 'JPEG'
            if image_file.name.lower().endswith('.png'):
                format = 'PNG'
            elif image_file.name.lower().endswith(('.webp')):
                format = 'WEBP'
                
            img.save(output_io, format=format, quality=85, optimize=True)
            
            # Возвращаем оптимизированное изображение
            output_io.seek(0)
            return ContentFile(output_io.getvalue(), name=image_file.name)
        except Exception as e:
            # В случае ошибки возвращаем оригинальное изображение
            print(f"Ошибка при оптимизации изображения: {e}")
            image_file.seek(0)
            return image_file

    def clean_image(self):
        """
        Проверяем размер изображения перед загрузкой
        """
        image = self.cleaned_data.get('image')
        if image:
            # Ограничение 5 МБ
            max_size = 5 * 1024 * 1024  # 5MB в байтах
            
            if image.size > max_size:
                # Если файл слишком большой, выдаем ошибку
                raise forms.ValidationError(
                    f"Изображение слишком большое. Максимальный размер: 5 МБ. "
                    f"Текущий размер: {image.size / (1024 * 1024):.2f} МБ."
                )
                
            # Проверяем формат файла
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            import os
            extension = os.path.splitext(image.name)[1].lower()
            
            if extension not in valid_extensions:
                raise forms.ValidationError(
                    f"Неподдерживаемый формат файла. Поддерживаемые форматы: {', '.join(valid_extensions)}"
                )
                
        return image

    def save(self, commit=True, product=None):
        """
        Переопределяем метод save для более надежной загрузки в S3
        """
        image = self.cleaned_data.get('image')
        if not image:
            return None
        
        try:
            # Создаем экземпляр ProductImage без сохранения в БД
            product_image = super().save(commit=False)
            
            # Если передан продукт, связываем с ним
            if product:
                product_image.product = product
            
            # Попытаемся оптимизировать изображение, но при ошибке используем оригинал
            try:
                optimized_image = self._optimize_image(image)
            except Exception as e:
                print(f"Не удалось оптимизировать изображение: {e}")
                image.seek(0)  # Перемотка файла в начало
                optimized_image = image
            
            # Используем стандартный механизм Django для сохранения в S3
            # Вместо прямого вызова storage.save
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            file_name = f"product_images/{timestamp}_{image.name.split('/')[-1]}"
            
            # Сохраняем временно файл в поле, но не сохраняем в БД
            product_image.image.save(
                file_name,
                optimized_image,
                save=False
            )
            
            # Сохраняем запись в БД, если требуется
            if commit:
                product_image.save()
                
            return product_image
            
        except Exception as e:
            import traceback
            print(f"Ошибка сохранения изображения: {e}")
            traceback.print_exc()
            raise
        
# FormSet для множественной загрузки изображений
ProductImageFormSet = forms.modelformset_factory(
    ProductImage,
    form=ProductImageForm,
    extra=5,  # Количество пустых форм
    max_num=10,  # Максимальное количество форм
)

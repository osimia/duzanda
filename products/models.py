# duzanda/products/models.py

from django.db import models
from accounts.models import User
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from duzanda.storage_backends import ProductImagesStorage
from duzanda.storage_backends import ProductImagesStorage

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    master = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='products',
        limit_choices_to={'role': 'master'}
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Старая цена')
    stock = models.PositiveIntegerField(default=1)
    SIZES = [
        ("XS", "XS"),
        ("S", "S"),
        ("M", "M"),
        ("L", "L"),
        ("XL", "XL"),
        ("XXL", "XXL"),
        ("3XL", "3XL"),
    ]
    sizes = models.CharField("Доступные размеры", max_length=100, blank=True, help_text="Выберите один или несколько размеров через запятую (например: S,M,L)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.master.username}"

    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(round((self.old_price - self.price) / self.old_price * 100))
        return None

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/', storage=ProductImagesStorage())
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"
        
    def get_s3_url(self):
        """
        Получить корректный URL для изображения из S3
        """
        if not self.image:
            return None
            
        url = self.image.url
        
        # Убедимся, что URL начинается с https://
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
            
        return url

    def get_direct_s3_url(self):
        """
        Получить прямой URL к изображению в S3 Selectel без использования Django Storage
        """
        from django.conf import settings
        from urllib.parse import quote
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not self.image or not self.image.name:
            logger.warning(f"Image for product {self.product_id} is None or has no name")
            return None
            
        # Используем прямой URL формата Selectel Storage
        direct_storage_url = getattr(settings, 'SELECTEL_DIRECT_STORAGE_URL', None)
        
        # Если настроен прямой URL Selectel, используем его
        if direct_storage_url:
            try:
                # Получаем имя файла
                filename = self.image.name
                
                # Удаляем 'product_images/' если оно есть в имени файла
                if filename.startswith('product_images/'):
                    filename = filename[len('product_images/'):]
                
                # Кодируем имя файла для URL (обрабатываем спецсимволы)
                encoded_filename = quote(filename)
                
                # Формируем прямой URL в формате Selectel
                url = f"{direct_storage_url}/product_images/{encoded_filename}"
                
                logger.debug(f"Generated direct S3 URL: {url}")
                return url
            except Exception as e:
                logger.error(f"Error generating direct S3 URL: {str(e)}")
                # Если что-то пошло не так, пробуем стандартный метод
                try:
                    return self.image.url
                except Exception as e2:
                    logger.error(f"Error getting standard URL: {str(e2)}")
                    return None
        else:
            # Запасной вариант - используем обычный URL
            try:
                return self.image.url
            except Exception as e:
                logger.error(f"Error getting image URL: {str(e)}")
                return None
                return None

# Для добавления категорий по умолчанию

def create_default_categories(sender, **kwargs):
    from .models import Category
    defaults = [
        'Национальная одежда',
        'Украшения',
        'Аксессуары',
        'Обувь',
        'Домашний декор',
    ]
    for name in defaults:
        Category.objects.get_or_create(name=name)

@receiver(post_migrate)
def create_categories_signal(sender, **kwargs):
    if sender.name == 'products':
        create_default_categories(sender)

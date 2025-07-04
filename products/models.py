# duzanda/products/models.py

from django.db import models
from accounts.models import User
from django.db.models.signals import post_migrate
from django.dispatch import receiver

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
    image = models.ImageField(upload_to='product_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"

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

from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'old_price', 'stock', 'size']
        labels = {
            'category': 'Категория',
            'name': 'Название',
            'description': 'Описание',
            'price': 'Цена',
            'old_price': 'Старая цена',
            'stock': 'Количество',
            'size': 'Размер',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

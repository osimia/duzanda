from django import forms
from .models import Product

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
        # Сохраняем как строку через запятую
        return ','.join(sizes)

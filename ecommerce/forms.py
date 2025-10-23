from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'category', 'price', 'discount_price',
            'file_url', 'thumbnail', 'is_free', 'is_active', 'tags'
        ]

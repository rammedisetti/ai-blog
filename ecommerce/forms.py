from decimal import Decimal

from django import forms

from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'category', 'price', 'discount_price',
            'file_url', 'thumbnail', 'is_free', 'is_active', 'tags'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].required = False
        if self.instance and self.instance.pk:
            self.fields['thumbnail'].required = False

    def clean(self):
        cleaned_data = super().clean()
        is_free = cleaned_data.get('is_free')
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')

        if is_free:
            cleaned_data['price'] = Decimal('0.00')
            cleaned_data['discount_price'] = None
        else:
            if price is None:
                self.add_error('price', 'Price is required for paid products.')
            elif price < Decimal('0.00'):
                self.add_error('price', 'Price must be zero or positive.')

            if discount_price is not None:
                if discount_price < Decimal('0.00'):
                    self.add_error('discount_price', 'Discount price must be zero or positive.')
                elif price is not None and discount_price >= price:
                    self.add_error('discount_price', 'Discount price must be less than the regular price.')

        return cleaned_data

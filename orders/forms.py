from django import forms

from .models import Item, User, Order
from products.models import Product


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['product', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_available=True)
        self.fields['quantity'].initial = 1


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'  # ou especifique os campos que deseja incluir

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Precarregar os usuários se necessário
        self.fields['customer'].queryset = User.objects.all()

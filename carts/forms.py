from django import forms 
from orders.models import Order


class CreateOrderForm(forms.ModelForm): 
    class Meta: 
        model = Order 
        fields = ['payment_method', 'delivery_terms'] 
        labels = {
            'payment_method': 'Способ оплаты', 
            'delivery_terms': 'Условия доставки', 
        }
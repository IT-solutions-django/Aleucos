from django import forms
from .models import PaymentMethod, DeliveryTerm


class XlsxImportOrderForm(forms.Form):
    xlsx_file = forms.FileField(label='XLSX-файл') 
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.all(), 
        label='Способ оплаты',
        required=False
    )
    delivery_terms = forms.ModelChoiceField(
        queryset=DeliveryTerm.objects.all(),  
        label='Условия доставки',
        required=False
    )
    
    comment = forms.CharField(
        label='Комментарий',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
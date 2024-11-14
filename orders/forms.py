from django import forms
from .models import PaymentMethod, DeliveryTerm
from users.models import User
from django.contrib.auth.models import Group
from configs.models import Config


class XlsxImportOrderForm(forms.Form):
    xlsx_file = forms.FileField(label='XLSX-файл') 
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label='Клиент',
        required=True
    )
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

    def __init__(self, *args, user: User=None, **kwargs):
        super().__init__(*args, **kwargs)
        users_group_name = Config.get_instance().users_group_name
        users_group = Group.objects.get(name=users_group_name)
        if user.groups.filter(name=Config.get_instance().managers_group_name).exists():
            self.fields['user'].queryset = User.objects.filter(groups=users_group).filter(manager=user)
        else: 
            self.fields['user'].queryset = User.objects.filter(groups=users_group)

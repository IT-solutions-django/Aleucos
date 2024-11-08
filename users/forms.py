from django import forms
from .models import RegistrationRequest
from django.contrib.auth.models import Group
from configs.models import Config
from users.models import User


class RegistrationRequestForm(forms.Form): 
    name = forms.CharField(label='Имя', required=True)
    last_name = forms.CharField(label='Фамилия', required=True)
    patronymic = forms.CharField(label='Отчество')
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Номер телефона', max_length=20) 


class RegistrationRequestAdminForm(forms.ModelForm):
    class Meta:
        model = RegistrationRequest
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        managers_group = Group.objects.get(name=Config.get_instance().managers_group_name)  
        self.fields['manager'].queryset = User.objects.filter(groups=managers_group)
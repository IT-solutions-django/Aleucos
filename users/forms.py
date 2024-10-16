from django import forms


class RegistrationRequestForm(forms.Form): 
    name = forms.CharField(label='Имя', required=True)
    last_name = forms.CharField(label='Фамилия', required=True)
    patronymic = forms.CharField(label='Отчество')
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Номер телефона', max_length=20) 
from django import forms
from .models import RegistrationRequest
from django.contrib.auth.models import Group
from configs.models import Config
from users.models import User


class RequestForm(forms.Form): 
    name = forms.CharField(
        max_length=50, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'contacts__form-input contacts__form-input-cont', 
            'placeholder': 'Введите имя'
        })
    )
    phone = forms.CharField(
        max_length=20, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'contacts__form-input contacts__form-input--tel contacts__form-input-cont', 
        })
    )
    email = forms.EmailField(
        max_length=100, 
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'contacts__form-input contacts__form-input-cont', 
            'placeholder': 'Email'
        })
    )
    message = forms.CharField(
        max_length=250, 
        required=False, 
        widget=forms.Textarea(attrs={
            'class': 'contacts__form-input contacts__form-textarea contacts__form-input-cont', 
            'placeholder': 'Введите текст сообщения'
        })
    )


class RegistrationRequestAdminForm(forms.ModelForm):
    class Meta:
        model = RegistrationRequest
        fields = ['last_name', 'first_name', 'patronymic', 'phone', 'email', 'to_save', 'manager', 'city']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.user.groups.filter(name=Config.get_instance().managers_group_name).exists():
            self.fields['manager'].widget = forms.HiddenInput()

        if self.user.groups.filter(name=Config.get_instance().head_of_sales_group_name).exists():
            self.fields['to_save'].widget = forms.HiddenInput()

        if self.is_closed: 
            for value in self.fields.values(): 
                value.disabled = True

        managers_group = Group.objects.get(name=Config.get_instance().managers_group_name)  
        self.fields['manager'].queryset = User.objects.filter(groups=managers_group)
        

class ClientRegistrationForm(forms.ModelForm): 
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'patronymic', 'phone', 'email', 'city']


class StaffRegistrationForm(forms.ModelForm): 
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'patronymic', 'groups', 'phone', 'email', 'position', 'photo', 'work_start_date', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        staff_groups_names = (
            Config.get_instance().managers_group_name, 
            Config.get_instance().admins_group_name, 
            Config.get_instance().head_of_sales_group_name,
        )
        staff_groups = Group.objects.filter(name__in=staff_groups_names)

        if self.fields.get('groups'):
            self.fields['groups'].queryset = staff_groups

    def save(self, commit=True):
        user: User = super().save(commit=False)
        user.is_staff = True
        user.save()

        if commit:
            user.save()
            self.save_m2m()  
        return user
    

class LoginForm(forms.Form):
    email = forms.EmailField(
        label = 'Электронная почта', 
        widget = forms.EmailInput(
            attrs = {
                'placeholder': 'Введите электронную почту', 
                'class': 'login__input'
            }
        )
    )
    password = forms.CharField(
        min_length=5, 
        label='Пароль', 
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Введите пароль', 
                'class': 'login__input'
            }
        )
    )
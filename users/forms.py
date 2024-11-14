from django import forms
from .models import RegistrationRequest
from django.contrib.auth.models import Group
from configs.models import Config
from users.models import User


class RegistrationRequestAdminForm(forms.ModelForm):
    class Meta:
        model = RegistrationRequest
        fields = ['last_name', 'first_name', 'patronymic', 'phone', 'email', 'to_save', 'manager']

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
        fields = ['last_name', 'first_name', 'patronymic', 'phone', 'email']


class StaffRegistrationForm(forms.ModelForm): 
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'patronymic', 'groups', 'phone', 'email', 'position', 'photo', 'work_start_date']

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
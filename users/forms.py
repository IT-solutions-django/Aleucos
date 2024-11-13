from django import forms
from .models import RegistrationRequest
from django.contrib.auth.models import Group
from configs.models import Config
from users.models import User


class RegistrationRequestAdminForm(forms.ModelForm):
    class Meta:
        model = RegistrationRequest
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # if self.user.groups.filter(name=Config.get_instance().managers_group_name).exists():
        #     self.fields['manager'].widget = forms.HiddenInput()

        # if self.user.groups.filter(name=Config.get_instance().head_of_sales_group_name).exists():
        #     self.fields['to_save'].widget = forms.HiddenInput()

        print(type(self))
        managers_group = Group.objects.get(name=Config.get_instance().managers_group_name)  
        self.fields['manager'].queryset = User.objects.filter(groups=managers_group)
        
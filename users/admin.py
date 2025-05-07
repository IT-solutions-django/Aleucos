from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models.query import QuerySet
from django.http import HttpRequest
from .filters import (
    StaffGroupFilter,
    IsWithManager, 
    IsClosed
)
from configs.models import Config
from .services import generate_random_password
from .tasks import send_email_to_new_user_task
from .models import (
    Position, 
    UserProxy, 
    StaffProxy, 
    RegistrationRequest, 
    City
)
from .forms import (
    RegistrationRequestAdminForm, 
    ClientRegistrationForm, 
    StaffRegistrationForm
)
from Aleucos.crm import crm
from Aleucos.elastic_log_handler import log_customer_update


@admin.register(UserProxy)
class UserAdmin(admin.ModelAdmin):
    list_display = ['pk', 'email', 'first_name', 'last_name', 'organization_name', 'inn', 'kpp', 'full_address', 'phone', 'manager', 'discount']
    list_filter = [
        IsWithManager
    ]
    form = ClientRegistrationForm

    def save_model(self, request, obj: UserProxy, form, change):
        if not change: 
            obj.manager = request.user

            # Сначала проверяем, был ли указан пароль в форме
            if form.cleaned_data.get('password'):
                obj.set_password(form.cleaned_data['password'])
            else:
                raw_password = generate_random_password()
                obj.set_password(raw_password)
                # Отправляем email только если пароль был сгенерирован автоматически
                send_email_to_new_user_task.delay(obj.email, raw_password)

            super().save_model(request, obj, form, change)
            obj.groups.add(Group.objects.get(name=Config.get_instance().users_group_name))
            super().save_model(request, obj, form, change)

            responsible_user_email = obj.manager.email
            responsible_user_id = crm.get_user_id(responsible_user_email) 

            id_in_amocrm = crm.create_contact(
                name = obj.get_fullname(), 
                responsible_user_id = responsible_user_id, 
                email = obj.email, 
                phone = obj.phone
            )
            obj.id_in_amocrm = id_in_amocrm
            obj.save()
            return

        if 'password' in form.changed_data:
            obj.set_password(obj.password)  
        super().save_model(request, obj, form, change)
        
        # Логируем изменение данных клиента
        if change:
            log_customer_update(obj, request.user)

    def get_queryset(self, request):
        users_group_name = Config.get_instance().users_group_name
        managers_group_name = Config.get_instance().managers_group_name

        qs = super().get_queryset(request).filter(groups__name=users_group_name)
        if request.user.groups.filter(name=managers_group_name).exists():
            return qs.filter(manager=request.user)
        return qs 
    

@admin.register(StaffProxy)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'email', 'first_name', 'last_name', 'position', 'phone', 'is_active']
    list_filter = [
        StaffGroupFilter,
        'is_superuser', 
    ]
    form = StaffRegistrationForm

    def save_model(self, request, obj, form, change):
        if not change: 
            obj.manager = request.user

        if 'password' in form.changed_data:
            obj.set_password(obj.password)  
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request).exclude(groups__name=Config.get_instance().users_group_name)
        return qs 
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.user = request.user
        return form


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title'] 


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'last_name', 'first_name', 'patronymic', 'manager', 'created_at', 'is_closed']
    ordering = ['-created_at']
    form = RegistrationRequestAdminForm
    list_filter = [
        IsClosed,
    ]

    def get_queryset(self, request):
        if request.user.groups.filter(name=Config.get_instance().managers_group_name).exists():
            return super().get_queryset(request).filter(manager=request.user)
        else: 
            return super().get_queryset(request)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.user = request.user
        form.is_closed = obj.is_closed if hasattr(obj, 'is_closed') else False
        return form
    

@admin.register(City)
class CityAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'name'] 
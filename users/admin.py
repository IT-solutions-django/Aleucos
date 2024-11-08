from django.contrib import admin
from .filters import GroupFilter
from .models import Position, UserProxy, StaffProxy, RegistrationRequest
from configs.models import Config
from .forms import RegistrationRequestAdminForm


@admin.register(UserProxy)
class UserAdmin(admin.ModelAdmin):
    list_display = ['pk', 'email', 'first_name', 'last_name','phone', 'manager']
    list_filter = [
        GroupFilter,
        'is_active', 
    ]

    def save_model(self, request, obj, form, change):
        if not change: 
            obj.manager = request.user

        if 'password' in form.changed_data:
            obj.set_password(obj.password)  
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        users_group_name = Config.get_instance().users_group_name
        managers_group_name = Config.get_instance().managers_group_name

        qs = super().get_queryset(request).filter(groups__name=users_group_name)
        if request.user.groups.filter(name=managers_group_name).exists():
            return qs.filter(manager=request.user)
        return qs 
    

@admin.register(StaffProxy)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'email', 'first_name', 'last_name', 'position', 'phone']
    list_filter = [
        GroupFilter,
        'is_superuser', 
        'is_active', 
    ]

    def save_model(self, request, obj, form, change):
        if not change: 
            obj.manager = request.user

        if 'password' in form.changed_data:
            obj.set_password(obj.password)  
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request).exclude(groups__name=Config.get_instance().users_group_name)
        return qs 


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title'] 


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'last_name', 'first_name', 'patronymic', 'created_at']
    ordering = ['-created_at']
    form = RegistrationRequestAdminForm
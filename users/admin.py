from django.contrib import admin
from .filters import GroupFilter
from .models import Position, UserProxy, StaffProxy, RegistrationRequest
from Aleucos import settings


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
        qs = super().get_queryset(request).filter(groups__name=settings.USERS_GROUP_NAME)
        if request.user.groups.filter(name=settings.MANAGERS_GROUP_NAME).exists():
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
        qs = super().get_queryset(request).exclude(groups__name=settings.USERS_GROUP_NAME)
        return qs 


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title'] 


@admin.register(RegistrationRequest)
class RequstrationRequestAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'first_name', 'last_name', 'patronymic', 'email', 'phone']

from django.contrib.auth.models import Group 
from django.contrib.admin import SimpleListFilter
from configs.models import Config
from users.models import User


class StaffGroupFilter(SimpleListFilter):
    title = 'Группа'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        groups = Group.objects.all().exclude(name=Config.get_instance().users_group_name)
        return [(group.id, group.name) for group in groups]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(groups__id__exact=self.value())
        return queryset


class IsWithManager(SimpleListFilter):
    title = 'Менеджер'
    parameter_name = 'manager'

    def lookups(self, request, model_admin):
        manager_group = Group.objects.get(name=Config.get_instance().managers_group_name)
        managers = User.objects.filter(groups__in=(manager_group,))

        return [(manager.id, manager.email) for manager in managers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(manager__id__exact=self.value())
        return queryset
    

class IsClosed(SimpleListFilter): 
    title = 'Обработано'
    parameter_name = 'is_closed' 

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'), 
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes': 
            return queryset.filter(is_closed=True)
        elif self.value() == 'no':
            return queryset.filter(is_closed=False)
        return queryset
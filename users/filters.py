from django.contrib.auth.models import Group 
from django.contrib.admin import SimpleListFilter



class GroupFilter(SimpleListFilter):
    title = 'Группа'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        groups = Group.objects.all()
        return [(group.id, group.name) for group in groups]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(groups__id__exact=self.value())
        return queryset

from django.contrib.admin import SimpleListFilter


class HasClient(SimpleListFilter):
    title = 'Связан с клиентом'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'), 
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes': 
            return queryset.filter(user__isnull=False)
        elif self.value() == 'no':
            return queryset.filter(user__isnull=True)
        return queryset
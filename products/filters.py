from django.contrib.admin import SimpleListFilter
from Aleucos.settings import DEFAULT_IMAGE_PATH
from .models import Product


class PriceRangeFilter(SimpleListFilter):
    title = 'Ценовой диапазон'
    parameter_name = 'price_range'

    def lookups(self, request, model_admin):
        return (
            ('low', 'Низкая (0-500₽)'),
            ('medium', 'Средняя (500-1000₽)'),
            ('high', 'Высокая (>1000₽)'), 
        )

    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(price_before_200k__lt=500)
        elif self.value() == 'medium': 
            return queryset.filter(price_before_200k__gte=500, price_before_200k__lt=1000)
        elif self.value() == 'high':
            return queryset.filter(price_before_200k__gte=1000)
        return queryset


class WeightRangeFilter(SimpleListFilter):
    title = 'Диапазон веса'
    parameter_name = 'weight_range' 

    def lookups(self, request, model_admin):
        return (
            ('light', 'Легкий (<0.2 кг)'), 
            ('medium', 'Средний (0.2-0.6 кг)'),
            ('heavy', 'Тяжёлый (>0.6 кг)'),
            ('unknown', 'Неизвестно')
        )

    def queryset(self, request, queryset):
        if self.value() == 'light': 
            return queryset.filter(weight__lt=0.2)
        elif self.value() == 'medium':
            return queryset.filter(weight__gte=0.2, weight__lte=0.6)
        elif self.value() == 'heavy':
            return queryset.filter(weight__gt=0.6) 
        elif self.value() == 'unknown':  
            return queryset.filter(weight=None)
        return queryset
    

class HasNotesFilter(SimpleListFilter):
    title = 'Наличие заметок'
    parameter_name = 'has_notes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть'), 
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(notes='')
        elif self.value() == 'no': 
            return queryset.filter(notes='')
        return queryset 
    

class RemainsRangeFilter(SimpleListFilter):
    title = 'Остатки'
    parameter_name = 'remains_range'

    def lookups(self, request, model_admin):
        return (
            ('low', 'Низкие (0-200)'),
            ('medium', 'Средние (200-800)'),
            ('high', 'Высокие (>800)'), 
        )

    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(remains__lt=200)
        elif self.value() == 'medium': 
            return queryset.filter(remains__gte=200, remains__lt=800)
        elif self.value() == 'high':
            return queryset.filter(remains__gte=800)
        return queryset
    

class HasPhotoFilter(SimpleListFilter):
    title = 'Наличие фото'
    parameter_name = 'has_photo'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть'), 
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(photo=DEFAULT_IMAGE_PATH)
        elif self.value() == 'no': 
            return queryset.filter(photo=DEFAULT_IMAGE_PATH)
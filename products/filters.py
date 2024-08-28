from django.contrib.admin import SimpleListFilter
from Aleucos.settings import DEFAULT_IMAGE_PATH
from .models import Product


class PriceRangeFilter(SimpleListFilter):
    title = 'price range'
    parameter_name = 'price_range'

    def lookups(self, request, model_admin):
        return (
            ('low', 'Low (0-500₽)'),
            ('medium', 'Medium (500-1000₽)'),
            ('high', 'High (>1000₽)'), 
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
    title = 'weight range'
    parameter_name = 'weight_range' 

    def lookups(self, request, model_admin):
        return (
            ('light', 'Light (<0.2 kg)'), 
            ('medium', 'Medium (0.2-0.6 kg)'),
            ('heavy', 'Heavy (>0.6 kg)'),
            ('unknown', 'Unknown')
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
    

class FirstLetterFilter(SimpleListFilter):
    title = 'title initial'
    parameter_name = 'title_initial' 
 
    def lookups(self, request, model_admin): 
        initials = set()
        for title in Product.objects.values_list('title', flat=True):
            if title:
                initials.add(title[0].upper()) 
        return sorted((letter, letter) for letter in initials)

    def queryset(self, request, queryset): 
        if self.value():
            return queryset.filter(title__startswith=self.value().upper())
        return queryset
    

class HasNotesFilter(SimpleListFilter):
    title = 'has image'
    parameter_name = 'has_image'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'), 
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(notes='')
        elif self.value() == 'no': 
            return queryset.filter(notes='')
        return queryset 
    

class RemainsRangeFilter(SimpleListFilter):
    title = 'remains range'
    parameter_name = 'remains_range'

    def lookups(self, request, model_admin):
        return (
            ('low', 'Low (0-200)'),
            ('medium', 'Medium (200-800)'),
            ('high', 'High (>800)'), 
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
    title = 'has photo'
    parameter_name = 'has_photo'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'), 
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(photo=DEFAULT_IMAGE_PATH)
        elif self.value() == 'no': 
            return queryset.filter(photo=DEFAULT_IMAGE_PATH)
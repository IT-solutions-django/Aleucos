from django.contrib import admin
from django.contrib.admin import SimpleListFilter

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


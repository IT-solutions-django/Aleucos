from django.contrib import admin
from .models import Brand, Product 


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title']
    list_filter = ['title']
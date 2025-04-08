from django.contrib import admin
from .models import (
    CompanyInfo, 
    ContactsManager,
)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['__str__']


@admin.register(ContactsManager)
class ContactsManagerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email']
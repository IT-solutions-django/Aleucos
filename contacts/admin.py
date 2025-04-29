from django.contrib import admin
from .models import (
    CompanyInfo, 
    ContactsManager,
    Partner,
)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['__str__']


@admin.register(ContactsManager)
class ContactsManagerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email']\
    

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'logo']
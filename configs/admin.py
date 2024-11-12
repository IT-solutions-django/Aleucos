from django.contrib import admin
from .models import Config


@admin.register(Config)
class SettingsAdmin(admin.ModelAdmin): 
    list_display = ['title']

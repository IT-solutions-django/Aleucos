from django.urls import path
from .views import *


app_name = 'amo_webhooks' 


urlpatterns = [
    path('status_lead', status_lead_view, name='status_lead'),
    path('responsible_lead', responsible_lead_view, name='responsible_lead'), 
]
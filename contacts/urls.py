from django.urls import path
from .views import *


app_name = 'contacts' 


urlpatterns = [
    path('contacts/', ContactsView.as_view(), name='contacts'),
    path('about/', AboutView.as_view(), name='about'),
]
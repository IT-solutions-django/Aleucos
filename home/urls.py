from django.urls import path
from .views import *


app_name = 'home'


urlpatterns = [
    path('', HomeView.as_view(), name='home'), 

    path('api/save_registration_request/', ContactFormView.as_view(), name='save_request'),
]
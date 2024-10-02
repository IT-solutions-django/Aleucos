from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *


app_name = 'users' 


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'), 
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), 
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),

    path('account/', AccountView.as_view(), name='account'),
    path('registration-request/', RegistrationRequestView.as_view(), name='registration_request'),
]
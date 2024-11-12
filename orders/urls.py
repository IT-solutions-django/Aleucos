from django.urls import path
from .views import *


app_name = 'orders' 


urlpatterns = [
    path('import-order-statuses/<str:manager_email>', ImportOrdersStatusView.as_view(), name='import_order_statuses'),
]
from django.urls import path
from .views import *


app_name = 'products'


urlpatterns = [
    path('products-list/', ProductsListView.as_view(), name='products_list'), 
]
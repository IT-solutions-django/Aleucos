from django.urls import path
from .views import *


app_name = 'products'


urlpatterns = [
    path('products-list/', ProductsListView.as_view(), name='products_list'), 
    path('price-list-download/', DownloadPriceListView.as_view(), name='price_list_download')
]
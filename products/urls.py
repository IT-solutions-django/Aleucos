from django.urls import path
from .views import *


app_name = 'products'


urlpatterns = [
    path('products-list/', ProductsListView.as_view(), name='products_list'), 
    path('filters/', CatalogFiltersView.as_view(), name='filters'),

    path('import-products-statuses/', ImportProductsStatusView.as_view(), name='import_product_statuses'),
]
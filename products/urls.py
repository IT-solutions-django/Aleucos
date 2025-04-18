from django.urls import path
from .views import *


app_name = 'products'


urlpatterns = [
    path('products-list/', ProductsListView.as_view(), name='products_list'), 
    path('filters/', CatalogFiltersView.as_view(), name='filters'),    
    path('export-catalog/', ExportCatalogView.as_view(), name='export_catalog'),
    path('import-products-statuses/', ImportProductsStatusView.as_view(), name='import_product_statuses'),

    path('generate-articles-test/', SetArticlesIfNullView.as_view()),
    
    path('<slug:product_slug>/', ProductView.as_view(), name='product'),
]
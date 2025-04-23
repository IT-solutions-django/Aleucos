from django.urls import path
from .views import *


app_name = 'orders' 


urlpatterns = [
    path('import-order-statuses/<str:manager_email>', ImportOrdersStatusView.as_view(), name='import_order_statuses'),
    path('get-excel/<int:order_number>/', DownloadExcelVersion.as_view(), name='get_excel_version'),

    path('get-city/<int:user_id>', GetUserCityAPIView.as_view(), name='get-city'),
]
from django.shortcuts import render
from django.http import FileResponse, JsonResponse
from django.views import View
from .models import ImportOrderStatus
from users.models import User
from .models import Order
from .services import OrderExcelGenerator



class ImportOrdersStatusView(View): 
    def get(self, request, manager_email: str): 
        statuses = ImportOrderStatus.objects.all().filter(manager__email=manager_email)[:100]
        data = [
            {
                'time': status.time.strftime('%H:%M'), 
                'text': str(status), 
                'type': status.status_type
            }
            for status in statuses
        ]
        if not statuses:
            data = []
        return JsonResponse(data, safe=False)
    

class GetUserCityAPIView(View): 
    def get(self, request, user_id: int): 
        user = User.objects.filter(pk=user_id).first()
        city = ''
        if user and user.city: 
            city = user.city 
        return JsonResponse({
            'city': city
        })
    

class DownloadExcelVersion(View): 
    """Выгрузка информации о заказе в Excel"""
    def get(self, request, order_number: int): 
        order = Order.objects.get(number=order_number) 
        OrderExcelGenerator.export_order_to_xlsx(order)

        if order.info_excel: 
            try:
                file = order.info_excel.open('rb')
                response = FileResponse(file)
                filename = f"order_{order.number}.xlsx"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                return response
            except: 
                pass
        
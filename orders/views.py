from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from .models import ImportOrderStatus



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
from django.shortcuts import render
from django.views import View
from orders.models import Order
from .models import RegistrationRequest
from .forms import RegistrationRequestForm
from Aleucos.crm import crm 
from Aleucos import settings


class AccountView(View): 
    def get(self, request): 
        user = request.user
        orders = Order.objects.filter(user=user).order_by('-created_at')
        
        context =  {
            'orders': orders, 
            'manager': user.manager,
        }

        return render(request, 'users/account.html', context)
    

class RegistrationRequestView(View): 
    def get(self, request): 
        context = {
            'form': RegistrationRequestForm(),
        }

        return render(request, 'users/registration_request.html', context)
    
    def post(self, request): 
        first_name = request.POST.get('name')
        last_name = request.POST.get('last_name')
        patronymic = request.POST.get('patronymic')
        phone = request.POST.get('phone') 
        email = request.POST.get('email') 

        registration_request = RegistrationRequest.objects.create(
            first_name = first_name, 
            last_name = last_name, 
            patronymic = patronymic, 
            phone = phone, 
            email = email,
        )

        return render(request, 'users/registration_request_sent.html')
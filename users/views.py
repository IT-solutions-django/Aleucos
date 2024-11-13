from django.shortcuts import render
from django.views import View
from orders.models import Order
from .models import RegistrationRequest
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from Aleucos.crm import crm 
from Aleucos import settings


@method_decorator(login_required, name='dispatch')
class AccountView(View): 
    def get(self, request): 
        user = request.user
        orders = Order.objects.filter(user=user).order_by('-created_at')
        
        context =  {
            'orders': orders, 
            'manager': user.manager,
        }

        return render(request, 'users/account.html', context)
    
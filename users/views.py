from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView
from orders.models import Order
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import LoginForm
from django.contrib.auth import authenticate, login
from .forms import AccountFilterForm


@method_decorator(login_required, name='dispatch')
class AccountView(View): 
    def get(self, request): 
        user = request.user
        orders = Order.objects.filter(user=user).order_by('-created_at')
        filter_form = AccountFilterForm(request.GET)

        if filter_form.is_valid(): 
            cd = filter_form.cleaned_data 
            section = cd.get('sections') 
            
            if section and section != 'Все': 
                match section: 
                    case 'Сначала новые': 
                        orders = orders.order_by('-created_at') 
                    case 'Сначала старые': 
                        orders = orders.order_by('created_at')
        
        context =  {
            'orders': orders, 
            'manager': user.manager,
            'filter_form': filter_form,
        }

        return render(request, 'users/account.html', context)
    

class LoginView(FormView):
    template_name = 'registration/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('products:products_list')

    def form_valid(self, form: LoginForm):
        cd = form.cleaned_data
        email = cd['email']
        password = cd['password']

        user = authenticate(self.request, email=email, password=password)
        if user:
            login(self.request, user)
            return super().form_valid(form)

        form.add_error(None, "Неверный логин или пароль")
        return self.form_invalid(form)
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
from datetime import datetime
from django.http import JsonResponse


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


            dates_string = request.GET.get('dates')
            start_date_original = None 
            end_date_original = None

            if dates_string:
                if '—' in dates_string: 
                    date_parts = dates_string.split(' — ')
                    start_date_original, end_date_original = date_parts
                    start_date = '-'.join(list(reversed(start_date_original.split('.'))))
                    end_date = '-'.join(list(reversed(end_date_original.split('.'))))

                    orders = orders.filter(
                        created_at__date__gte=start_date,
                        created_at__date__lte=end_date
                    )
                else: 
                    start_date = end_date = dates_string
            
        context =  {
            'orders': orders, 
            'manager': user.manager,
            'filter_form': filter_form,
            'start_date': start_date_original,
            'end_date': end_date_original,
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
    

class JuridicalInfoView(View):
    def post(self, request):
        organization_name = request.POST.get('organization-name')
        inn = request.POST.get('inn')
        kpp = request.POST.get('kpp')
        full_address = request.POST.get('full-address')

        request.user.organization_name = organization_name
        request.user.inn = inn
        request.user.kpp = kpp
        request.user.full_address = full_address
        request.user.save()

        return JsonResponse({'success': True})


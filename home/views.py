from django.http import JsonResponse
from django.shortcuts import render
from django.views import View 
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from users.forms import RequestForm
from users.models import RegistrationRequest, User
from configs.models import Config 
from django.contrib.auth.models import Group 
from Aleucos.crm import crm
from products.models import Product


class HomeView(View): 
    template_name = 'home/home.html' 

    def get(self, request): 
        popular_products = Product.objects.all()[:10]
        context = {
            'contact_form': RequestForm(),
            'popular_products': popular_products,
        }
        return render(request, self.template_name, context)


@method_decorator(csrf_exempt, name='dispatch')
class ContactFormView(View): 
    @csrf_exempt
    def post(self, request): 
        form: RequestForm = RequestForm(request.POST)
        if form.is_valid(): 
            cd = form.cleaned_data 
            name, phone, email, message = cd['name'], cd['phone'], cd['email'], cd['message']

            last_request = RegistrationRequest.objects.order_by('-id').first()
            manager_group = Group.objects.get(name=Config.get_instance().managers_group_name)
            if last_request and last_request.manager:
                last_manager = last_request.manager  # TODO: Обязательно отрефакторить логику фильтрации по группам пользователей
                next_manager = User.objects.filter(groups__in=(manager_group,)).filter(id__gt=last_manager.id).filter(is_active=True).order_by('id').first()
                if not next_manager:
                    next_manager = User.objects.filter(groups__in=(manager_group,)).order_by('id').first()
            else:
                next_manager = User.objects.filter(groups__in=(manager_group,)).order_by('id').first()

            responsible_user_id = crm.get_user_id(
                user_email=next_manager.email
            )

            new_request: RegistrationRequest = RegistrationRequest(
                first_name=name if name else None, 
                phone=phone, 
                email=email, 
                manager=next_manager,
            )
            new_request.save()
            contact_id = crm.create_contact(
                name=new_request.first_name, 
                responsible_user_id=responsible_user_id, 
                email=new_request.email, 
                phone=new_request.phone
            )
            crm.create_lead(
                f'Новый клиент с сайта: {email}', 
                responsible_user_id=responsible_user_id, 
                contact_id=contact_id, 
                from_the_very_first_status=True
            )

            return JsonResponse({'status': 'ok'})
        else:
            return JsonResponse({"error": form.errors}, status=400)

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
from carts.services import Cart


class HomeView(View): 
    template_name = 'home/home.html' 

    def get(self, request): 
        popular_products = Product.objects.all().filter(is_hit=True)

        cart_data = request.cart.to_dict()
        products_in_cart = {
            article: item['quantity'] 
            for article, item in cart_data['products'].items()
        }

        for product in popular_products:
            product.quantity_in_cart = request.cart[Cart.KeyNames.PRODUCTS].get(str(product.article), {}).get(Cart.KeyNames.QUANTITY, 0)

        context = {
            'contact_form': RequestForm(),
            'popular_products': popular_products,
            'products_in_cart': products_in_cart
        }
        return render(request, self.template_name, context)


@method_decorator(csrf_exempt, name='dispatch')
class ContactFormView(View): 
    @csrf_exempt
    def post(self, request): 
        try:
            form: RequestForm = RequestForm(request.POST)
            if form.is_valid(): 
                cd = form.cleaned_data 
                name, phone, email, message = cd['name'], cd['phone'], cd['email'], cd['message']

                print(name, phone, email, message)

                last_request = RegistrationRequest.objects.order_by('-id').first()
                manager_group = Group.objects.get(name=Config.get_instance().managers_group_name)
                if last_request and last_request.manager:
                    last_manager = last_request.manager  
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
                print(form.errors)
                return JsonResponse({"error": form.errors}, status=400)
        except Exception as e: 
            print(f'Ошибка при сохранении заявки: {str(e)}')
            return JsonResponse({'status': 'not ok'})
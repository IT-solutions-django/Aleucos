from django.http import JsonResponse
from django.shortcuts import render
from django.views import View 
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from users.forms import RequestForm
from users.models import RegistrationRequest


class HomeView(View): 
    template_name = 'home/home.html' 

    def get(self, request): 
        context = {
            'contact_form': RequestForm()
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

            new_request = RegistrationRequest(
                first_name=name, 
                phone=phone, 
                email=email
            )
            new_request.save()

            return JsonResponse({'status': 'ok'})
        else:
            return JsonResponse({"error": form.errors}, status=400)

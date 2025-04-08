from django.shortcuts import render
from django.views import View 
from .models import ContactsManager


class ContactsView(View): 
    template_name = 'contacts/contacts.html' 

    def get(self, request): 
        managers = ContactsManager.objects.all()
        context = {
            'managers': managers,
        }
        return render(request, self.template_name, context)
    

class AboutView(View): 
    template_name = 'contacts/about.html' 

    def get(self, request): 
        context = {
            '1': '1', 
        }
        return render(request, self.template_name, context)
from django.shortcuts import render
from django.views import View 


class ContactsView(View): 
    template_name = 'contacts/contacts.html' 

    def get(self, request): 
        context = {
            '1': '1',
        }
        return render(request, self.template_name, context)
    

class AboutView(View): 
    template_name = 'contacts/about.html' 

    def get(self, request): 
        context = {
            '1': '1', 
        }
        return render(request, self.template_name, context)
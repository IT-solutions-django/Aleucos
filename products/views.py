from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from elasticsearch_dsl.query import MultiMatch
from Aleucos.settings import MEDIA_ROOT
from django.contrib import messages
import os
from .models import Product
from .forms import SearchAndFilterForm
from .services import get_paginated_collection
from .documents import ProductDocument


class HomeView(View):
    def get(self, request): 
        return redirect('products:products_list')


class ProductsListView(View):
    template_name = 'products/products_list.html'

    def get(self, request, *args, **kwargs):
        form = SearchAndFilterForm(request.GET)

        if form.is_valid():
            cd = form.cleaned_data

            products = Product.objects.all()
            
            search_text = cd.get('q') 
            selected_sections = cd.get('sections') 
            if search_text or selected_sections:
                products = ProductDocument.search()
                if search_text:
                    products = products.query(
                        MultiMatch(query=search_text, fields=['title', 'description', 'notes'])
                    )
                if selected_sections: 
                    if 'новинки' in selected_sections: 
                        products = products.query('match', notes='NEW')
                    if 'акции' in selected_sections: 
                        products = products.query('match', notes='акция')
                    if 'скидки' in selected_sections: 
                        products = products.query('match', notes='скидка')

                products = products.to_queryset()
                
            if not search_text and not selected_sections: 
                products = Product.objects.all()

            selected_categories = cd.get('categories')
            if selected_categories:
                products = products.filter(category__id__in=selected_categories)

            selected_brands = cd.get('brands')
            if selected_brands:
                products = products.filter(brand__id__in=selected_brands)
            
            price_min = cd.get('price_min')
            if price_min is not None:
                products = products.filter(price_before_200k__gte=price_min)

            price_max = cd.get('price_max')
            if price_max is not None:
                products = products.filter(price_before_200k__lte=price_max)

            is_in_stock = cd.get('is_in_stock')
            if is_in_stock: 
                products = products.filter(is_in_stock=is_in_stock)


        paginated_products = get_paginated_collection(request, products, 48)

        context = {
            'form': form,
            'products': paginated_products,
        }

        return render(request, self.template_name, context) 
    

class DownloadPriceListView(View): 
    def get(self, request) -> FileResponse | HttpResponse: 
        price_list_path = os.path.join(MEDIA_ROOT, 'tmpf', 'price_list.xlsx') 

        try:
            response = FileResponse(open(price_list_path, 'rb'))
            return response
        except FileNotFoundError:
            messages.error(request, 'Ошибка: файл не найден', extra_tags=messages.ERROR)
        except PermissionError:
            messages.error(request, 'Ошибка доступа', extra_tags=messages.ERROR)
        except Exception: 
            messages.error(request, 'Ошибка', extra_tags=messages.ERROR)
        return redirect('products:products_list')
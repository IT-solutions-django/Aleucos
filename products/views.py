from django.shortcuts import render
from django.views import View
from elasticsearch_dsl.query import MultiMatch
from .models import Product
from .forms import SearchAndFilterForm
from .services import get_paginated_collection
from .documents import ProductDocument


class ProductsListView(View):
    template_name = 'products/products_list.html'

    def get(self, request, *args, **kwargs):
        form = SearchAndFilterForm(request.GET)
        print(f'Форма валидна? {form.is_valid()}')

        if form.is_valid():
            search_text = form.cleaned_data.get('q') 
            if search_text:
                products = ProductDocument.search().query(
                    MultiMatch(query=search_text, fields=['title', 'description', 'notes'])
                ).to_queryset()
            else: 
                products = Product.objects.all()
            

            selected_categories = form.cleaned_data.get('categories')
            if selected_categories:
                products = products.filter(category__id__in=selected_categories)
            
            selected_brands = form.cleaned_data.get('brands')
            if selected_brands:
                products = products.filter(brand__id__in=selected_brands)
            
            price_min = form.cleaned_data.get('price_min')
            price_max = form.cleaned_data.get('price_max')
            if price_min is not None:
                products = products.filter(price_before_200k__gte=price_min)
            if price_max is not None:
                products = products.filter(price_before_200k__lte=price_max)

            is_in_stock = form.cleaned_data.get('is_in_stock') 
            if is_in_stock is not None: 
                products = products.filter(is_in_stock=is_in_stock)

        paginated_products = get_paginated_collection(request, products, 50)

        context = {
            'form': form,
            'products': paginated_products,
        }

        return render(request, self.template_name, context)
from django.shortcuts import render
from django.views import View
from elasticsearch_dsl.query import MultiMatch, Q
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
            cd = form.cleaned_data

            products = ProductDocument.search()
            
            search_text = cd.get('q') 
            if search_text:
                products = products.query(
                    MultiMatch(query=search_text, fields=['title', 'description', 'notes'])
                )

            selected_sections = cd.get('sections') 
            if selected_sections: 
                if 'новинки' in selected_sections: 
                    products = products.query('match', notes='NEW')
                if 'акции' in selected_sections: 
                    products = products.query('match', notes='акция')
                if 'скидки' in selected_sections: 
                    products = products.query('match', notes='скидка')
                

            products = products.to_queryset()

            selected_categories = cd.get('categories')
            if selected_categories:
                products = products.filter(category__id__in=selected_categories)
            
            selected_brands = cd.get('brands')
            if selected_brands:
                products = products.filter(brand__id__in=selected_brands)
            
            price_min = cd.get('price_min')
            price_max = cd.get('price_max')
            if price_min is not None:
                products = products.filter(price_before_200k__gte=price_min)
            if price_max is not None:
                products = products.filter(price_before_200k__lte=price_max)

            is_in_stock = cd.get('is_in_stock') 
            if is_in_stock is not None: 
                products = products.filter(is_in_stock=is_in_stock)
            

        paginated_products = get_paginated_collection(request, products, 50)

        context = {
            'form': form,
            'products': paginated_products,
        }

        return render(request, self.template_name, context)
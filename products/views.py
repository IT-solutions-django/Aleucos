from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from elasticsearch_dsl.query import MultiMatch
from carts.services import Cart
from django.core.paginator import Paginator
from .models import Product
from .forms import SearchAndFilterForm
from .documents import ProductDocument
from .models import ImportProductsStatus


class ImportProductsStatusView(View): 
    def get(self, request): 
        statuses = ImportProductsStatus.objects.all()[:100]
        data = [
            {
                'time': status.time.strftime('%H:%M'), 
                'text': str(status), 
                'type': status.status_type
            }
            for status in statuses
        ]
        return JsonResponse(data, safe=False)


class ProductsListView(View):
    template_name = 'products/products_list.html'

    def get(self, request):
        form = SearchAndFilterForm(request.GET)
        if form.is_valid():
            cd = form.cleaned_data

            products = Product.objects.all()
            
            search_text = cd.get('q') 
            selected_section = cd.get('sections') 
            
            if search_text or (selected_section and selected_section != 'все'):
                products = ProductDocument.search()
                if search_text:
                    products = products.query(
                        MultiMatch(query=search_text, fields=['title', 'description', 'notes'])
                    )
                if selected_section: 
                    if selected_section == 'новинки': 
                        products = products.query('match', notes='NEW')
                    elif selected_section == 'акции': 
                        products = products.query('match', notes='акция')
                    elif selected_section == 'скидки': 
                        products = products.query('match', notes='скидка')

                products = products.to_queryset()
                
            if not search_text and not selected_section: 
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


        cart_data = request.cart.to_dict()
        products_in_cart = {barcode: item['quantity'] for barcode, item in cart_data['products'].items()}

        for product in products:
            product.quantity_in_cart = request.cart[Cart.KeyNames.PRODUCTS].get(str(product.barcode), {}).get(Cart.KeyNames.QUANTITY, 0)

        page_number = request.GET.get('page', 1) 
        paginator = Paginator(products, 16)  
        page_obj = paginator.get_page(page_number)


        context = {
            'form': form,
            'products': page_obj, 
            'products_in_cart': products_in_cart
        }

        return render(request, self.template_name, context) 
    


class CatalogFiltersView(View): 
    def get(self, request):
        form = SearchAndFilterForm(request.GET)
        if form.is_valid():
            cd = form.cleaned_data

            products = Product.objects.all()
            
            search_text = cd.get('q') 
            selected_section = cd.get('sections') 
            
            if search_text or (selected_section and selected_section != 'все'):
                products = ProductDocument.search()
                if search_text:
                    products = products.query(
                        MultiMatch(query=search_text, fields=['title', 'description', 'notes'])
                    )
                if selected_section: 
                    if selected_section == 'новинки': 
                        products = products.query('match', notes='NEW')
                    elif selected_section == 'акции': 
                        products = products.query('match', notes='акция')
                    elif selected_section == 'скидки': 
                        products = products.query('match', notes='скидка')

                products = products.to_queryset()
                
            if not search_text and not selected_section: 
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

        if not products.exists(): 
            return JsonResponse({
                'products': None,
            })
        
        products = products.select_related('brand').all()
        
        page_number = request.GET.get('page', 1) 
        paginator = Paginator(products, 16)  
        page_obj = paginator.get_page(page_number)

        if not page_obj.object_list:
            return JsonResponse({
                'products': None,
            })

        products_json = [
        {
            'barcode': product.barcode,
            'title': product.title,
            'description': product.description,
            'photo': product.photo.url,
            'brand': product.brand.title, 
            'category': product.category.title, 
            'price_before_200k': product.price_before_200k, 
            'volume': product.volume, 
            'weight': product.weight, 
            'notes': product.notes, 
            'remains': product.remains,
        }
        for product in page_obj.object_list]

        return JsonResponse({
            'products': products_json,
            'has_next': page_obj.has_next(),  
            'has_previous': page_obj.has_previous(),  
            'current_page': page_obj.number,  
            'total_pages': paginator.num_pages,  
            'cart': request.cart.to_dict(),
        })
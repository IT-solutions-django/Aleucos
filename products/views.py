from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from elasticsearch_dsl.query import MultiMatch
from django.db.models.functions import Cast
from django.db.models import TextField
from carts.services import Cart
from django.core.paginator import Paginator
from .models import Product
from .forms import SearchAndFilterForm
from .documents import ProductDocument
from .models import ImportProductsStatus
from django.db.models import Q, Value
from django.db.models.functions import Greatest
from django.contrib.postgres.search import TrigramSimilarity
from django.template.loader import render_to_string 
from django.shortcuts import get_object_or_404
from configs.models import Config
from Aleucos import settings
from django.http import FileResponse
import os

from Aleucos.elastic_log_handler import log_product_sale, log_product_arrival


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
            barcode = cd.get('barcode')
            
            if search_text or (selected_section and selected_section != 'все'):
                if search_text:
                    products = products.annotate(
                        similarity=Greatest(
                            TrigramSimilarity('title', search_text),
                            TrigramSimilarity('description', search_text),
                            TrigramSimilarity('notes', search_text),
                            Value(0.0) 
                        )
                    ).filter(similarity__gt=0.1).order_by('-similarity')  

                if selected_section:
                    section_filters = {
                        'новинки': Q(notes__icontains='NEW'),
                        'акции': Q(notes__icontains='акция'),
                        'скидки': Q(notes__icontains='скидка'),
                    }
                    products = products.filter(section_filters.get(selected_section, Q()))

                if barcode:
                    products = products.annotate(
                        barcode_similarity=TrigramSimilarity('barcode', barcode)
                    ).filter(barcode_similarity__gt=0.2).order_by('-barcode_similarity')
                
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

            weight_min = cd.get('weight_min')
            if weight_min is not None:
                products = products.filter(weight__gte=weight_min)

            weight_max = cd.get('weight_max')
            if weight_max is not None:
                products = products.filter(weight__lte=weight_max)

            is_in_stock = cd.get('is_in_stock')
            if is_in_stock: 
                products = products.filter(is_in_stock=is_in_stock)


        cart_data = request.cart.to_dict()
        products_in_cart = {
            barcode: item['quantity'] 
            for barcode, item in cart_data['products'].items()
        }

        for product in products:
            product.quantity_in_cart = request.cart[Cart.KeyNames.PRODUCTS].get(str(product.barcode), {}).get(Cart.KeyNames.QUANTITY, 0)

        page_number = request.GET.get('page', 1) 
        paginator = Paginator(products, 16)  
        page_obj = paginator.get_page(page_number)

        context = {
            'form': form,
            'products': page_obj, 
            'products_in_cart': products_in_cart, 
            'search_text': search_text
        }

        return render(request, self.template_name, context) 
    


class CatalogFiltersView(View): 
    def get(self, request):
        form = SearchAndFilterForm(request.GET)

        print(f'Данные с формы: {form.data}')

        if form.is_valid():
            cd = form.cleaned_data

            products = Product.objects.all()
            
            search_text = cd.get('q') 
            selected_section = cd.get('sections') 
            barcode = cd.get('barcode')
            
            if search_text or (selected_section and selected_section != 'все'):
                if search_text:
                    products = products.annotate(
                        similarity=Greatest(
                            TrigramSimilarity('title', search_text),
                            TrigramSimilarity('description', search_text),
                            TrigramSimilarity('notes', search_text),
                            Value(0.0) 
                        )
                    ).filter(similarity__gt=0.1).order_by('-similarity')  

                if selected_section:
                    if selected_section in ('подешевле', 'подороже'): 
                        match selected_section: 
                            case 'подешевле': 
                                products = products.order_by('price_before_200k')
                            case 'подороже': 
                                products = products.order_by('-price_before_200k')
                    else:
                        section_filters = {
                            'новинки': Q(notes__icontains='NEW'),
                            'акции': Q(notes__icontains='акция'),
                            'скидки': Q(notes__icontains='скидка'),
                            'в наличии': Q(is_in_stock=True),
                        }
                        products = products.filter(section_filters.get(selected_section, Q()))

            if not search_text and not selected_section: 
                products = Product.objects.all()

            if barcode:
                products = products.filter(barcode__icontains=barcode)
            

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

            weight_min = cd.get('weight_min')
            if weight_min is not None:
                products = products.filter(weight__gte=weight_min)

            weight_max = cd.get('weight_max')
            if weight_max is not None:
                products = products.filter(weight__lte=weight_max)

            is_in_stock = cd.get('is_in_stock')
            if is_in_stock: 
                products = products.filter(is_in_stock=True)

            is_not_in_stock = cd.get('is_not_in_stock')
            if is_not_in_stock: 
                products = products.filter(is_in_stock=False)

        if not products.exists(): 
            return JsonResponse({
                'products': None,
            })
        
        products = products.select_related('brand').all()

        cart_data = request.cart.to_dict()
        products_in_cart = {
            barcode: item['quantity'] 
            for barcode, item in cart_data['products'].items()
        }

        for product in products:
            product.quantity_in_cart = request.cart[Cart.KeyNames.PRODUCTS].get(str(product.barcode), {}).get(Cart.KeyNames.QUANTITY, 0)
        
        page_number = request.GET.get('page', 1) 
        products = Paginator(products, 16)  
        products = products.get_page(page_number)

        if not products.object_list:
            return JsonResponse({
                'products': None,
                'pagination': None,
            })
        
        products_cards = render_to_string('products/includes/products_cards.html', {
            'products': products,
            'request': request,
        }) 
        pagination = render_to_string('products/includes/pagination.html', {
            'products': products,
            'request': request,
        }) 

        return JsonResponse({
            'cards': products_cards,
            'pagination': pagination,
            'products_in_cart': products_in_cart
        })
    

class ProductView(View): 
    template_name = 'products/product.html' 

    def get(self, request, product_slug: str): 
        print(f'Слаг: {product_slug}')
        
        # product = get_object_or_404(Product, slug=product_slug)
        product = Product.objects.filter(slug=product_slug).first()

        print(product.pk)

        similar_products = Product.objects.all().filter(category=product.category).exclude(pk=product.pk)

        cart_data = request.cart.to_dict()
        products_in_cart = {
            barcode: item['quantity'] 
            for barcode, item in cart_data['products'].items()
        }

        product.quantity_in_cart = request.cart[Cart.KeyNames.PRODUCTS].get(str(product.barcode), {}).get(Cart.KeyNames.QUANTITY, 0)

        for similar_product in similar_products:
            similar_product.quantity_in_cart = request.cart[Cart.KeyNames.PRODUCTS].get(str(similar_product.barcode), {}).get(Cart.KeyNames.QUANTITY, 0)

        print(product.pk)

        context = {
            'product': product,
            'similar_products': similar_products,
            'products_in_cart': products_in_cart
        }
        return render(request, self.template_name, context)
    

class ExportCatalogView(View): 
    def get(self, request): 
        filename = os.path.join(settings.MEDIA_ROOT, 'catalog', Config.get_instance().export_catalog_filename)
        try:
            response = FileResponse(open(filename, 'rb'))
            return response
        except FileNotFoundError:
            self.message_user(request, 'Файл для экспорта не найден', level='error')
            return redirect('admin:products_product_changelist')
        except PermissionError:
            self.message_user(request, 'Файл для экспорта не найден', level='error')
            return redirect('admin:products_product_changelist')
        except Exception: 
            self.message_user(request, 'Файл для экспорта не найден', level='error')
            return redirect('admin:products_product_changelist')
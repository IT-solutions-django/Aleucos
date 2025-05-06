from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.utils.decorators import method_decorator
from orders.models import Order, OrderItem
from products.models import Product
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services import Cart
from orders.models import DeliveryTerm, PaymentMethod
from loguru import logger
from users.models import City
from Aleucos.elastic_log_handler import log_product_sale


@method_decorator(login_required, name='dispatch')
class ChangeCartView(View):
    def post(self, request):
        cart = request.cart
        article: str = request.POST.get('article')
        raw_quantity = request.POST.get('quantity')
        append = bool(request.POST.get('append', False))

        try:
            quantity = int(raw_quantity)
        except ValueError: 
            return JsonResponse({
                'cart': cart.to_dict(), 
            })
        if not article: 
            JsonResponse({
                'error': 'отсутствует артикул'
            })
        product = Product.objects.filter(article=article).first() 
        if not product: 
            cart.remove(str(article))
            return JsonResponse({
                'cart': cart.to_dict(), 
            })
        if quantity < 0 and append == False:
            cart.change(product=product, quantity=-1)
            return JsonResponse({
                'cart': cart.to_dict(), 
            })
        if Cart.KeyNames.PRODUCTS not in cart:
            cart[Cart.KeyNames.PRODUCTS] = {}
        product_in_cart = cart[Cart.KeyNames.PRODUCTS].get(str(article))
        if product_in_cart is None: 
            new_quantity_in_cart = 1 
        else: 
            if append:
                new_quantity_in_cart = product_in_cart[Cart.KeyNames.QUANTITY] + quantity
            else:
                new_quantity_in_cart = quantity
            
        if product.remains - new_quantity_in_cart < 0:
            return JsonResponse({
                'error': f'количество товара ограничено: осталось {product.remains} единиц', 
                'cart': cart.to_dict(), 
            })
        cart.change(product=product, quantity=quantity, append=append)

        return JsonResponse({
            'cart': cart.to_dict(), 
        })
    

@method_decorator(login_required, name='dispatch')
class FlushCartView(View):
    def post(self, request):
        request.cart.flush()
        return JsonResponse({
            'success': 'true', 
        })
    

@method_decorator(login_required, name='dispatch')
class CartItemsView(View):
    def get(self, request):   
        delivery_terms = DeliveryTerm.objects.all()
        payment_methods = sorted(
            PaymentMethod.objects.all(),
            key=lambda x: (x.title == 'Другое', x.title)
        )


        cart = request.cart

        articles = list(cart['products'].keys())
        products = Product.objects.filter(article__in=articles).select_related('brand')
        products_by_article = {product.article: product for product in products}
        cart_product_list = list(products_by_article.values())
        cart_product_list.sort(key=lambda p: (p.brand.title if p.brand else '', p.title))


        context = {
            'cart': request.cart, 
            'cart_product_list': cart_product_list,
            'delivery_terms': delivery_terms,
            'payment_methods': payment_methods,
        }
        return render(request, 'carts/cart_items.html', context)
    

@method_decorator(login_required, name='dispatch')
class CheckCartView(View):
    def post(self, request):
        cart = request.cart
        errors = []

        if not cart.get(Cart.KeyNames.PRODUCTS):
            errors.append('Корзина пуста')

        articles_to_remove = []

        for article, product_data in list(cart[Cart.KeyNames.PRODUCTS].items()):
            try:
                product = Product.objects.get(article=article)
            except Product.DoesNotExist:
                errors.append(f'Товара с артикулом {article} больше нет в наличии. Недоступные товары не будут включены в заказ')
                articles_to_remove.append(article)
                continue

            quantity = product_data[Cart.KeyNames.QUANTITY]

            if quantity > product.remains:
                errors.append(f'Недостаточно товара "{product.title}" на складе: доступно {product.remains} шт., запрошено {quantity} шт. Недоступные товары не будут включены в заказ')
                request.cart.change(product, product.remains) 

        for article in articles_to_remove: 
            request.cart.remove(article)

        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors,
                'cart': request.cart.to_dict()
            })

        return JsonResponse({
            'success': True,
        })
    

@method_decorator(login_required, name='dispatch')
class CreateOrderView(View): 
    def post(self, request): 
        cart = request.cart 
        user_discount = request.user.discount / 100 if request.user.discount else 0
        final_price_coefficient = (1 - user_discount)

        if not cart.get(Cart.KeyNames.PRODUCTS): 
            return
        
        payment_method_id = request.POST.get('payment_method')
        delivery_terms_id = request.POST.get('delivery_terms')
        city = request.POST.get('city')
        comment = request.POST.get('comment')

        request.user.city = city 
        request.user.save()

        try:
            payment_method = PaymentMethod.objects.get(pk=payment_method_id)
            delivery_terms = DeliveryTerm.objects.get(pk=delivery_terms_id)
        except PaymentMethod.DoesNotExist:
            logger.error(f'Способа оплаты с ID={payment_method_id} не существует')
            return redirect('carts:cart_items')
        except DeliveryTerm.DoesNotExist: 
            logger.error(f'Способа оплаты с ID={payment_method_id} не существует')
            return redirect('carts:cart_items')
            
        manager = None
        if request.user.is_staff: 
            manager = request.user
        else: 
            manager = request.user.manager

        total_order_price = cart[Cart.KeyNames.TOTAL_CART_PRICE] * final_price_coefficient
        new_order = Order.objects.create(
            user=request.user, 
            total_price=total_order_price, 
            manager=manager, 
            payment_method=payment_method, 
            delivery_terms=delivery_terms,
            comment=comment,
            city=city
        )


        articles = list(cart[Cart.KeyNames.PRODUCTS].keys())
        products = Product.objects.filter(article__in=articles).select_related('brand')
        products_dict = {p.article: p for p in products}  

        if len(products) != len(articles):
            missing_articles = set(articles) - set(products_dict.keys())
            logger.error(f'Товары не найдены: {missing_articles}')
            return redirect('carts:cart_items')

        order_items = []
        for article, product_data in cart[Cart.KeyNames.PRODUCTS].items(): 

            product = products_dict[article]

            unit_price = product_data[Cart.KeyNames.UNIT_PRICE] * final_price_coefficient
            quantity = product_data[Cart.KeyNames.QUANTITY]
            total_product_price = product_data[Cart.KeyNames.TOTAL_PRODUCT_PRICE] * final_price_coefficient

            order_items.append(
                OrderItem(
                    article=article,
                    product_name=product.title,
                    brand_name=product.brand.title,
                    order=new_order, 
                    quantity=quantity, 
                    unit_price=unit_price, 
                    total_price=total_product_price
                )
            )

            product.remains -= quantity

            log_product_sale(
                product=product, 
                quantity=quantity, 
                manager_name=request.user.get_fullname
            )

            product.save()

        OrderItem.objects.bulk_create(order_items)
        new_order.create_pdf_bill()

        request.cart.flush()
        messages.success(request, f'Заказ №{new_order.number} успешно создан!', extra_tags=messages.SUCCESS)
        return redirect('users:account')

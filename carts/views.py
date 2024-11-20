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


@method_decorator(login_required, name='dispatch')
class ChangeCartView(View):
    def post(self, request):
        cart = request.cart
        barcode = int(request.POST.get('barcode'))
        raw_quantity = request.POST.get('quantity')
        append = bool(request.POST.get('append', False))

        try:
            quantity = int(raw_quantity)
        except ValueError: 
            return JsonResponse({
                'cart': cart.to_dict(), 
            })
        if not barcode: 
            JsonResponse({
                'error': 'отсутствует штрихкод'
            })
        product = Product.objects.filter(barcode=barcode).first() 
        if not product: 
            cart.remove(str(barcode))
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
        product_in_cart = cart[Cart.KeyNames.PRODUCTS].get(str(barcode))
        if product_in_cart is None: 
            new_quantity_in_cart = 1 
        else: 
            new_quantity_in_cart = product_in_cart[Cart.KeyNames.QUANTITY] + 1
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
        payment_methods = PaymentMethod.objects.all()
        cities = City.objects.all()

        context = {
            'cart': request.cart, 
            'delivery_terms': delivery_terms,
            'payment_methods': payment_methods,
            'cities': cities
        }
        return render(request, 'carts/cart_items.html', context)
    

@method_decorator(login_required, name='dispatch')
class CheckCartView(View):
    def post(self, request):
        cart = request.cart
        errors = []

        if not cart.get(Cart.KeyNames.PRODUCTS):
            errors.append('Корзина пуста')

        barcodes_to_remove = []

        for barcode, product_data in list(cart[Cart.KeyNames.PRODUCTS].items()):
            try:
                product = Product.objects.get(barcode=barcode)
            except Product.DoesNotExist:
                errors.append(f'Товара со штрихкодом {barcode} больше нет в наличии. Недоступные товары не будут включены в заказ')
                barcodes_to_remove.append(barcode)
                continue

            quantity = product_data[Cart.KeyNames.QUANTITY]

            if quantity > product.remains:
                errors.append(f'Недостаточно товара "{product.title}" на складе: доступно {product.remains} шт., запрошено {quantity} шт. Недоступные товары не будут включены в заказ')
                request.cart.change(product, product.remains) 

        for barcode in barcodes_to_remove: 
            request.cart.remove(barcode)

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

        if not cart.get(Cart.KeyNames.PRODUCTS): 
            return
        
        payment_method_id = request.POST.get('payment_method')
        delivery_terms_id = request.POST.get('delivery_terms')
        city_id = request.POST.get('city')
        comment = request.POST.get('comment')

        try:
            payment_method = PaymentMethod.objects.get(pk=payment_method_id)
            delivery_terms = DeliveryTerm.objects.get(pk=delivery_terms_id)
            city = City.objects.get(pk=city_id)
        except PaymentMethod.DoesNotExist:
            logger.error(f'Способа оплаты с ID={payment_method_id} не существует')
            return redirect('carts:cart_items')
        except DeliveryTerm.DoesNotExist: 
            logger.error(f'Способа оплаты с ID={payment_method_id} не существует')
            return redirect('carts:cart_items')
        except City.DoesNotExist: 
            logger.error(f'Города с ID={city_id} не существует')
            return redirect('carts:cart_items')
            
        total_order_price = cart[Cart.KeyNames.TOTAL_CART_PRICE]
        new_order = Order.objects.create(
            user=request.user, 
            total_price=total_order_price, 
            manager=request.user.manager, 
            payment_method=payment_method, 
            delivery_terms=delivery_terms,
            comment=comment,
            city=city
        )

        for barcode, product_data in cart[Cart.KeyNames.PRODUCTS].items(): 

            product = Product.objects.get(barcode=barcode)

            unit_price = product_data[Cart.KeyNames.UNIT_PRICE] 
            quantity = product_data[Cart.KeyNames.QUANTITY]
            total_product_price = product_data[Cart.KeyNames.TOTAL_PRODUCT_PRICE] 

            OrderItem.objects.create(
                product_name=product.title,
                brand_name=product.brand.title,
                order=new_order, 
                quantity=quantity, 
                unit_price=unit_price, 
                total_price=total_product_price
            )

            product.remains -= quantity
            product.save()
        new_order.create_pdf_bill()

        request.cart.flush()
        messages.success(request, f'Заказ №{new_order.number} успешно создан!', extra_tags=messages.SUCCESS)
        return redirect('users:account')

from django.utils.deprecation import MiddlewareMixin
import json
from .services import Cart


class CartMiddleware(MiddlewareMixin):
    def process_request(self, request):
        cart_data = request.session.get('cart', {})
        request.cart = Cart(cart_data)


    def process_response(self, request, response):
        if getattr(request, 'cart', None) is None:
            return response
        if request.cart.changed:
            request.session['cart'] = request.cart.to_dict()
            request.session.save()
        return response


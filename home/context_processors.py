from users.forms import RequestForm


def global_context(request):
    cart_data = request.cart.to_dict()
    is_cart_page = False
    if 'cart-items' in request.path: 
        is_cart_page = True
    return {
        'contact_form': RequestForm(),
        'cart_positions_count': len(cart_data['products']), 
        'is_cart_page': is_cart_page
    }
from users.forms import RequestForm


def global_context(request):
    cart_data = request.cart.to_dict()
    
    return {
        'contact_form': RequestForm(),
        'cart_positions_count': len(cart_data['products'])
    }
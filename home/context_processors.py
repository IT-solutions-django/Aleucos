from users.forms import RequestForm
from contacts.models import CompanyInfo


def global_context(request):
    cart_data = request.cart.to_dict()
    is_cart_page = False
    company_info = CompanyInfo.get_instance()
    if 'cart-items' in request.path: 
        is_cart_page = True
    return {
        'contact_form': RequestForm(),
        'cart_positions_count': len(cart_data['products']), 
        'is_cart_page': is_cart_page, 
        'company_info': company_info
    }
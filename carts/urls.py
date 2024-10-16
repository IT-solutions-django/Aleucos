from django.urls import path
from .views import *


app_name = 'carts' 


urlpatterns = [
    path('cart-items/', CartItemsView.as_view(), name='cart_items'),
    path('change/', ChangeCartView.as_view(), name='change'),
    path('flush/', FlushCartView.as_view(), name='flush_cart'),
    path('check-cart/', CheckCartView.as_view(), name='check_cart'), 

    path('create-order/', CreateOrderView.as_view(), name='create_order'),
]
from django import template
from Aleucos import settings
from products.models import Product

register = template.Library()

@register.filter
def product_image_url(barcode: str) -> str:
    product = Product.objects.filter(barcode=barcode).first()
    if product:
        return product.photo.url
    return settings.DEFAULT_IMAGE_PATH

@register.filter
def product_title(barcode: str) -> str: 
    product = Product.objects.filter(barcode=barcode).first()
    if product:
        return product.title
    return "Товар не найден"

@register.filter
def product_remains(barcode: str) -> int: 
    product = Product.objects.filter(barcode=barcode).first()
    if product:
        return product.remains
    return 0
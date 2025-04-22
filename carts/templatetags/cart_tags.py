from django import template
from Aleucos import settings
from products.models import Product

register = template.Library()

@register.filter
def product_image_url(article: str) -> str:
    product = Product.objects.filter(article=article).first()
    if not product:
        return settings.DEFAULT_IMAGE_PATH
    if product.photo:
        return product.photo.url 
    return settings.DEFAULT_IMAGE_PATH

@register.filter
def product_title(article: str) -> str: 
    product = Product.objects.filter(article=article).first()
    if product:
        return product.title
    return "Товар не найден"

@register.filter
def product_remains(article: str) -> int: 
    product = Product.objects.filter(article=article).first()
    if product:
        return product.remains
    return 0


@register.filter
def get_product_photo_by_name(product_name: str) -> str: 
    product = Product.objects.filter(title=product_name).first()
    if product and product.photo:
        return product.photo.url 
    return settings.DEFAULT_IMAGE_PATH


@register.filter 
def product_barcode(article: str) -> str | None: 
    product = Product.objects.filter(article=article).first()
    if product: 
        if product.barcode: 
            return product.barcode 
    return '–'

@register.filter
def product_brand(article: str) -> str | None: 
    product = Product.objects.filter(article=article).first()
    if product: 
        if product.brand:
            return product.brand 
    return '–'
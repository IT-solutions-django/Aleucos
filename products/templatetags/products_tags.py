from django import template


register = template.Library()


@register.filter(name='price_format')
def price_format(value: str):
    try:
        value = float(value)
        return f"{value:,}".replace(',', ' ')
    except (ValueError, TypeError):
        return value 
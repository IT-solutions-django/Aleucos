from django import template


register = template.Library()


@register.filter(name='price_format')
def price_format(value):
    try:
        # Преобразуем в float, если это строка
        num = float(value) if isinstance(value, str) else float(value)
        
        # Проверяем количество знаков после запятой
        if '.' in str(value):
            decimal_part = str(value).split('.')[1]
            if len(decimal_part) > 6:
                num = round(num, 2)
        
        # Форматируем с пробелами в качестве разделителей тысяч
        formatted = "{:,.2f}".format(num) if isinstance(num, float) else "{:,}".format(num)
        return formatted.replace(',', ' ').replace('.00', '')  # Убираем .00 для целых чисел
    except (ValueError, TypeError):
        return value
    

@register.filter
def apply_discount(price, discount):
    return price_format(float(price) * (1 - discount / 100))
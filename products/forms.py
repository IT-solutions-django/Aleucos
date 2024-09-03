from django import forms

from products.services import get_all_model_objects, get_max_product_price
from .models import Brand, Category


class XlsxImportForm(forms.Form):
    xlsx_file = forms.FileField() 


class SearchAndFilterForm(forms.Form):
    max_product_price = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.max_product_price = get_max_product_price()
        self.fields['price_max'].widget.attrs['placeholder'] = f'{self.max_product_price} ₽'
        
        self.fields['categories'].choices = [(category.id, category.title) for category in get_all_model_objects(Category)]
        self.fields['brands'].choices = [(brand.id, brand.title) for brand in get_all_model_objects(Brand)]

    q = forms.CharField(
        max_length=100, 
        required=False, 
        label='Введите запрос', 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Найти товар'
        })
    )

    categories = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    price_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Мин. цена',
        widget=forms.NumberInput(
            attrs={ 
                'class': 'form-control', 
                'placeholder': '0 ₽', 
                'min': 0,
                'step': 100,
                'type': 'text',
            }
        ), 
    )
    
    price_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={ 
                'class': 'form-control', 
                'min': 0,
                'step': 100,
            }
        ), 
    )

    brands = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    is_in_stock = forms.BooleanField(
        required=False,
        label_suffix='',
        label='В наличии',
        widget=forms.CheckboxInput()
    )

    sections = forms.MultipleChoiceField(
        choices=(
            ('новинки', 'Новинки'),
            ('акции', 'Акции'),
            ('скидки', 'Скидки'),
        ),
        widget=forms.CheckboxSelectMultiple(), 
        required=False
    )
 
    def clean_price_max(self): 
        cd = self.cleaned_data
        price_min = cd.get('price_min')
        price_max = cd.get('price_max')
        if price_max and price_min: 
            if price_min > price_max: 
                raise forms.ValidationError('Максимальная цена не может быть меньше минимальной') 
        return price_max
from django import forms

from .services import get_all_model_objects, get_max_product_price
from .models import Brand, Category


class XlsxImportProductsForm(forms.Form):
    xlsx_file = forms.FileField() 


class SearchAndFilterForm(forms.Form):
    max_product_price = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.max_product_price = round(get_max_product_price(), 0)
        self.fields['price_max'].widget.attrs['placeholder'] = f'До {self.max_product_price} ₽'
        
        self.fields['categories'].choices = [(category.id, category.title) for category in get_all_model_objects(Category)]
        self.fields['brands'].choices = [(brand.id, brand.title) for brand in get_all_model_objects(Brand)]

    q = forms.CharField(
        max_length=100, 
        required=False, 
        label='Введите запрос', 
        widget=forms.TextInput(attrs={
            'id': 'searchInput',
            'class': 'navbar__search-input filter-input',
            'placeholder': 'Поиск по сайту'
        })
    )

    categories = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'sidebar__section-checkbox filter-input'
            }
        ),
        required=False
    )

    price_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Мин. цена',
        widget=forms.NumberInput(
            attrs={ 
                'class': 'sidebar__price-input filter-input', 
                'placeholder': 'От 0 ₽', 
                'min': 0,
                'step': 100,
            }
        ), 
    )
    
    price_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={ 
                'class': 'sidebar__price-input filter-input', 
                'min': 0,
                'step': 100,
            }
        ), 
    )

    brands = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'sidebar__section-checkbox filter-input'
            }
        ),
        required=False
    )

    is_in_stock = forms.BooleanField(
        required=False,
        label_suffix='',
        label='В наличии',
        widget=forms.CheckboxInput(
            attrs={
                'class': 'sidebar__section-checkbox filter-input'
            }
        )
    )

    sections = forms.ChoiceField(
        choices=(
            ('все', 'все'),
            ('новинки', 'новинки'),
            ('акции', 'акции'),
            ('скидки', 'скидки'),
        ),
        widget=forms.RadioSelect(
            attrs={
                'class': 'topic-input filter-input'
            }, 
        ), 
        required=False, 
    )
 
    def clean_price_max(self): 
        cd = self.cleaned_data
        price_min = cd.get('price_min')
        price_max = cd.get('price_max')
        if price_max and price_min: 
            if price_min > price_max: 
                raise forms.ValidationError('Максимальная цена не может быть меньше минимальной') 
        return price_max
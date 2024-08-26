from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render

from .forms import XlsxImportForm
from .models import Brand, Product 
from .services import import_products_from_xlsx, ProductImportError


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title']
    list_filter = ['title']
    search_fields = ['title']


@admin.register(Product) 
class ProductAdmin(admin.ModelAdmin): 
    list_display = ['barcode', 'brand', 'title', 'volume', 'weight', 'photo',
                    'price_before_200k', 'price_after_200k', 'price_after_500k'] 
    search_fields = ['brand__title', 'title', 'barcode']

    change_list_template = 'products/product_change_list.html'

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('import-products-from-xlsx/', self.import_products_from_xlsx),
        ]
        return my_urls + urls

    def import_products_from_xlsx(self, request):
        context = admin.site.each_context(request)
        if request.method == 'POST':
            xlsx_file = request.FILES['xlsx_file']

            updated_products_count, errors = import_products_from_xlsx(xlsx_file)

            if errors:
                for error in errors:
                    self.message_user(request, error, level='error')

            self.message_user(request, f'Добавлено или обновлено {updated_products_count} товаров')
            return redirect('admin:products_product_changelist')

        context['form'] = XlsxImportForm()
        return render(request, 'products/add_products_form.html', context=context)
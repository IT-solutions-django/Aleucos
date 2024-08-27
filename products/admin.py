from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from django.core.files.storage import default_storage
from django.conf import settings
import os

from .forms import XlsxImportForm
from .models import Brand, Product 
from .tasks import import_products_from_xlsx_task


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
        context['form'] = XlsxImportForm()
        
        if request.method == 'POST':
            xlsx_file = request.FILES['xlsx_file']
            filename = f'tmp/{xlsx_file.name}'

            try:
                if default_storage.exists(filename): 
                    default_storage.delete(filename)
            except PermissionError: 
                self.message_user(request, 'Подождите немного, загрузка данных прошлого xlsx-файла ещё не окончена', level='error')
                return render(request, 'products/add_products_form.html', context=context)
            
            xlsx_file_path = default_storage.save(filename, xlsx_file)
            xlsx_file_full_path = os.path.join(settings.MEDIA_ROOT, xlsx_file_path)

            import_products_from_xlsx_task.delay(xlsx_file_full_path, request.user.pk)

            self.message_user(request, 'Импорт товаров запущен в фоновом режиме. Уведомления доступны в разделе Home - Recent actions')
            return redirect('admin:products_product_changelist')

        return render(request, 'products/add_products_form.html', context=context)
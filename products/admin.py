from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from django.core.files.storage import default_storage
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
import os
from .forms import XlsxImportForm
from .models import Brand, Product, Category, ImportStatus
from .tasks import import_products_from_xlsx_task
from .filters import (PriceRangeFilter, WeightRangeFilter, 
                      HasNotesFilter,  RemainsRangeFilter, HasPhotoFilter)
from .services import ImportStatusService


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title']
    list_filter = ['title']
    search_fields = ['title']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title']
    list_filter = ['title']
    search_fields = ['title']


@admin.register(ImportStatus)
class ImportStatusAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'text', 'time']
    list_filter = ['text']


@admin.register(Product) 
class ProductAdmin(admin.ModelAdmin): 
    list_display = ['barcode', 'brand', 'title', 'description', 'volume', 'weight', 'photo',
                    'price_before_200k', 'price_after_200k', 'price_after_500k'] 
    search_fields = ['brand__title', 'title', 'barcode']
    list_filter = (
        'is_in_stock',
        PriceRangeFilter,
        WeightRangeFilter,
        HasNotesFilter, 
        RemainsRangeFilter,
        HasPhotoFilter,
        'brand',
    )

    change_list_template = 'products/product_change_list.html'

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('import-products-from-xlsx/', self.import_products_from_xlsx),
            path('view-logs/', self.view_logs_file),
            path('status-of-import/', self.view_import_status)
        ]
        return my_urls + urls

    @method_decorator(staff_member_required)
    def view_logs_file(self, request) -> FileResponse | None:
        log_file_path = os.path.join('logs', 'logs.log')

        try:
            response = FileResponse(open(log_file_path, 'rb'))
            return response
        except FileNotFoundError:
            self.message_user(request, 'Файл с логами не найден.', level='error')
            return redirect('admin:products_product_changelist')
        except PermissionError:
            self.message_user(request, 'Ошибка доступа', level='error')
        except Exception: 
            self.message_user(request, 'Необработанное исключение', level='error')
            
    @method_decorator(staff_member_required)
    def view_import_status(self, request) -> HttpResponse: 
        context = admin.site.each_context(request) 
        context['import_statuses'] = ImportStatusService.get_all_statuses()
        return render(request, 'products/status_of_import.html', context)
    
    @method_decorator(staff_member_required)
    def import_products_from_xlsx(self, request) -> HttpResponse:
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

            self.message_user(request, 'Импорт товаров запущен в фоновом режиме. Логи будут доступны по окончании процесса')
            return redirect('admin:products_product_changelist')

        return render(request, 'products/add_products_form.html', context=context)

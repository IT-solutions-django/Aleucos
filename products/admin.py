from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from django.core.files.storage import default_storage
from Aleucos import settings
from django.http import FileResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
import os
from .forms import XlsxImportProductsForm
from .models import Brand, Product, Category, ImportProductsStatus, WatermarkConfig, ProductType
from .tasks import import_products_from_xlsx_task
from .filters import (PriceRangeFilter, WeightRangeFilter, 
                      HasNotesFilter,  RemainsRangeFilter, HasPhotoFilter)
from .services import ImportProductsStatusService, CatalogExporter
from configs.models import Config
from Aleucos.elastic_log_handler import log_product_arrival


def is_admin_or_superuser(user):
    return user.is_superuser or user.groups.filter(name=Config.get_instance().admins_group_name).exists()


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


@admin.register(Product) 
class ProductAdmin(admin.ModelAdmin): 
    list_display = ['article', 'barcode', 'brand', 'title', 'volume', 'weight', 'price_before_200k', 'price_after_200k', 'price_after_500k',
                     'photo', 'title_russian',
                     'is_in_stock', 'remains', 'will_arrive_at', 'slug',] 
    search_fields = ['article', 'brand__title', 'title', 'barcode']
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
            path('import_catalog/', self.import_catalog, name='import_catalog'),
            path('export_catalog/', self.export_catalog, name='export_catalog'),
            path('view-logs/', self.view_logs_file, name='view_logs'),
            path('status-of-products-import/', self.view_import_status, name='status_of_products_import')
        ]
        return my_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['is_admin_or_superuser'] = is_admin_or_superuser(request.user)

        return super().changelist_view(request, extra_context=extra_context)

    @method_decorator(user_passes_test(is_admin_or_superuser), name='view_logs_file')
    def view_logs_file(self, request) -> FileResponse | HttpResponse:
        log_file_path = os.path.join('logs', 'logs.log')

        try:
            response = FileResponse(open(log_file_path, 'rb'))
            return response
        except FileNotFoundError:
            self.message_user(request, 'Файл с логами не найден.', level='error')
        except PermissionError:
            self.message_user(request, 'Ошибка доступа', level='error')
        except Exception: 
            self.message_user(request, 'Необработанное исключение', level='error')
        return redirect('admin:products_product_changelist')
            
    @method_decorator(user_passes_test(is_admin_or_superuser), name='view_import_status')
    def view_import_status(self, request) -> HttpResponse: 
        context = admin.site.each_context(request) 
        context['import_statuses'] = ImportProductsStatusService.get_all_statuses()
        return render(request, 'products/status_of_import.html', context)
    
    @method_decorator(user_passes_test(is_admin_or_superuser), name='import_products_from_xlsx')
    def import_catalog(self, request) -> HttpResponse:
        context = admin.site.each_context(request)
        context['form'] = XlsxImportProductsForm()
        context['is_admin_or_superuser'] = is_admin_or_superuser(request.user)
        
        if request.method == 'POST':
            xlsx_file = request.FILES['xlsx_file']
            filename = os.path.join('catalog', Config.get_instance().import_catalog_filename)

            try:
                if default_storage.exists(filename): 
                    default_storage.delete(filename)
            except PermissionError: 
                self.message_user(request, 'Подождите немного, загрузка данных прошлого xlsx-файла ещё не окончена', level='error')
                return render(request, 'products/add_products_form.html', context=context)
            
            xlsx_file_path = default_storage.save(filename, xlsx_file)
            xlsx_file_full_path = os.path.join(settings.MEDIA_ROOT, xlsx_file_path)

            import_products_from_xlsx_task.delay(
                xlsx_file_path=xlsx_file_full_path, 
                manager_name=request.user.get_fullname(),
            )

            self.message_user(request, 'Импорт товаров запущен в фоновом режиме. Логи будут доступны по окончании процесса')
            return redirect('admin:status_of_products_import')

        return render(request, 'products/add_products_form.html', context=context)

    def export_catalog(self, request) -> HttpResponse:
        filename = os.path.join(settings.MEDIA_ROOT, 'catalog', Config.get_instance().export_catalog_filename)
        try:
            response = FileResponse(open(filename, 'rb'))
            return response
        except FileNotFoundError:
            self.message_user(request, 'Файл для экспорта не найден', level='error')
            return redirect('admin:products_product_changelist')
        except PermissionError:
            self.message_user(request, 'Файл для экспорта не найден', level='error')
            return redirect('admin:products_product_changelist')
        except Exception: 
            self.message_user(request, 'Файл для экспорта не найден', level='error')
            return redirect('admin:products_product_changelist')
        
    def save_model(self, request, obj, form, change):
        if change:  
            old_obj = Product.objects.get(pk=obj.pk)
            old_remains = old_obj.remains
            new_remains = obj.remains

            if new_remains > old_remains:
                log_product_arrival(
                    product=obj, 
                    quantity= new_remains - old_remains, 
                    manager_name=request.user.get_fullname()
                )

        super().save_model(request, obj, form, change)


@admin.register(ImportProductsStatus)
class Admin(admin.ModelAdmin): 
    list_display = ['pk', 'text', 'status_type']
    list_filter = ['text']
    search_fields = ['text']


@admin.register(WatermarkConfig)
class WatermarkConfigAdmin(admin.ModelAdmin): 
    pass


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin): 
    list_display = ['title']
    search_fields = ['title']
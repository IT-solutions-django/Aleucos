from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from django.core.files.storage import default_storage
from django.conf import settings
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
import os
from .forms import XlsxImportOrderForm
from .models import OrderStatus, Order, OrderItem, ImportOrderStatus, DeliveryTerm, PaymentMethod
from .tasks import import_orders_from_xlsx_task
from Aleucos import settings
from users.models import User


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin): 
    list_display = ['id', 'title',]


class OrderItemInline(admin.TabularInline): 
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'number', 'user', 'total_price', 'comment', 'status']

    inlines = [OrderItemInline]  
    
    change_list_template = 'orders/order_change_list.html'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        current_user = request.user
        if request.user.groups.filter(name=settings.MANAGERS_GROUP_NAME).exists():
            customers = User.objects.filter(manager=current_user)
            return qs.filter(user__in=customers)
        return qs

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-order-from-xlsx/', self.import_orders_from_xlsx, name='import_order_from_xlsx'),
            path('status-of-order-import/', self.view_import_status, name='status_of_order_import'),
        ]
        return my_urls + urls

    @method_decorator(staff_member_required)
    def import_orders_from_xlsx(self, request) -> HttpResponse:
        context = admin.site.each_context(request)
        context['form'] = XlsxImportOrderForm()

        if request.method == 'POST':
            xlsx_file = request.FILES['xlsx_file']
            filename = os.path.join('tmp', 'order_list.xlsx')

            try:
                if default_storage.exists(filename):
                    default_storage.delete(filename)
            except PermissionError:
                self.message_user(request, 'Подождите немного, загрузка данных прошлого xlsx-файла ещё не окончена', level='error')
                return render(request, 'orders/add_orders_form.html', context=context)
            
            xlsx_file_path = default_storage.save(filename, xlsx_file)
            xlsx_file_full_path = os.path.join(settings.MEDIA_ROOT, xlsx_file_path)

            import_orders_from_xlsx_task.delay(xlsx_file_full_path)

            self.message_user(request, 'Создание заказа запущено в фоновом режиме')
            return redirect('admin:status_of_order_import')

        return render(request, 'orders/add_order_form.html', context=context)
    
    @method_decorator(staff_member_required)
    def view_import_status(self, request) -> HttpResponse: 
        context = admin.site.each_context(request) 
        current_user = request.user

        if current_user.groups.filter(name=settings.MANAGERS_GROUP_NAME).exists():
            customers = User.objects.filter(manager=current_user)
            orders = Order.objects.filter(user__in=customers)
            import_statuses = ImportOrderStatus.objects.filter(order__in=orders)
        else: 
            import_statuses = ImportOrderStatus.objects.all()

        
        context['import_statuses'] = import_statuses
        return render(request, 'orders/status_of_import.html', context)



@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'product', 'order', 'quantity', 'unit_price', 'total_price']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title']


@admin.register(DeliveryTerm)
class DeliveryTermAdmin(admin.ModelAdmin): 
    list_display = ['pk', 'title']


# @admin.register(ImportOrderStatus)
# class ImportOrderStatusAdmin(admin.ModelAdmin): 
#     list_display = ['pk', 'text', 'time']
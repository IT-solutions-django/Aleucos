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
from configs.models import Config
from .filters import HasClient


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin): 
    list_display = ['id', 'title',]


class OrderItemInline(admin.TabularInline): 
    model = OrderItem
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name=Config.get_instance().managers_group_name).exists():
            return [field.name for field in self.model._meta.fields if field.name != 'quantity']
        return super().get_readonly_fields(request, obj)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'number', 'user', 'total_price', 'comment', 'status']
    list_filter = [
        HasClient
    ]
    inlines = [OrderItemInline]  
    change_list_template = 'orders/order_change_list.html'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        current_user = request.user
        if request.user.groups.filter(name=Config.get_instance().managers_group_name).exists():
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
        context['form'] = XlsxImportOrderForm(user=request.user)

        if request.method == 'POST':
            form = XlsxImportOrderForm(request.POST, request.FILES, user=request.user)
            
            if form.is_valid():
                xlsx_file = form.cleaned_data['xlsx_file']
                payment_method = form.cleaned_data.get('payment_method')
                delivery_terms = form.cleaned_data.get('delivery_terms')
                city = form.cleaned_data.get('city')
                comment = form.cleaned_data.get('comment')
                user = form.cleaned_data.get('user')
                print(type(user))
                print(user)

                filename = os.path.join('tmp', 'order_list.xlsx')

                try:
                    if default_storage.exists(filename):
                        default_storage.delete(filename)
                except PermissionError:
                    self.message_user(request, 'Подождите немного, загрузка данных прошлого xlsx-файла ещё не окончена', level='error')
                    return render(request, 'orders/add_orders_form.html', context=context)
                
                xlsx_file_path = default_storage.save(filename, xlsx_file)
                xlsx_file_full_path = os.path.join(settings.MEDIA_ROOT, xlsx_file_path)


                import_orders_from_xlsx_task.delay(
                    xlsx_file_path=xlsx_file_full_path, 
                    manager_email=request.user.email, 
                    payment_method_id=payment_method.pk, 
                    delivery_terms_id=delivery_terms.pk, 
                    city_id=city.pk,
                    comment=comment, 
                    user_id=user.pk
                )

                self.message_user(request, 'Создание заказа запущено в фоновом режиме')
                return redirect('admin:status_of_order_import')
            else: 
                self.message_user(request, 'Неверные данные', level='error')
                return render(request, 'orders/add_orders_form.html', context=context)

        return render(request, 'orders/add_order_form.html', context=context)
    
    @method_decorator(staff_member_required)
    def view_import_status(self, request) -> HttpResponse: 
        context = admin.site.each_context(request) 
        current_user = request.user

        import_statuses = ImportOrderStatus.objects.filter(manager=request.user)

        
        context['import_statuses'] = import_statuses
        return render(request, 'orders/status_of_import.html', context)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin): 
    list_display = ['title']


@admin.register(DeliveryTerm)
class DeliveryTermAdmin(admin.ModelAdmin): 
    list_display = ['title']


@admin.register(ImportOrderStatus)
class ImportOrderStatusAdmin(admin.ModelAdmin): 
    list_display = ['id', 'time', 'text', 'manager']
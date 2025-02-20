import random
import string
from django.db import models
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.dispatch import receiver
from Aleucos.crm import crm
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
import tempfile
import os
from django.core.files.base import ContentFile
from users.models import User
from .pdf_generator.services import generate_pdf_bill
from users.models import City



class OrderStatus(models.Model):
    title = models.CharField(_('Название'), max_length=100)

    class Meta:
        verbose_name = _('Статус')
        verbose_name_plural = _('Статусы')

    def __str__(self) -> str:
        return self.title


class PaymentMethod(models.Model):
    title = models.CharField(_('Название'), max_length=100)

    class Meta:
        verbose_name = _('Способ оплаты')
        verbose_name_plural = _('Способы оплаты')

    def __str__(self):
        return self.title
    

class DeliveryTerm(models.Model):
    title = models.CharField(_('Название'), max_length=100)

    class Meta:
        verbose_name = _('Условие доставки')
        verbose_name_plural = _('Условия доставки')

    def __str__(self):
        return self.title


class Order(models.Model):
    number = models.CharField(_('Номер заказа'), max_length=16)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name=_('Пользователь'), null=True, blank=True)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managers_orders', verbose_name=_('Менеджер'))
    id_in_amocrm = models.BigIntegerField(_('ID в amoCRM'), null=True)
    total_price = models.DecimalField(_('Итоговая цена'), decimal_places=2, max_digits=14, default=0)
    percentage_discount = models.DecimalField(_('Процент скидки'), decimal_places=2, max_digits=5, default=0, 
                                              validators=[
            MinValueValidator(0),  MaxValueValidator(100)
        ])
    is_discount_applied = models.BooleanField(_('Скидка применена'), default=False)
    status = models.ForeignKey(OrderStatus, on_delete=models.SET_NULL, null=True, default=1, verbose_name=_('Статус'))
    is_paid = models.BooleanField(_('Оплачено'), default=False)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    comment = models.TextField(_('Комментарий'), blank=True, null=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_DEFAULT, default=1, verbose_name=_('Способ оплаты'))
    delivery_terms = models.ForeignKey(DeliveryTerm, on_delete=models.SET_DEFAULT, default=1, verbose_name=_('Условия доставки'))
    pdf_bill = models.FileField(_('Счёт'), upload_to='orders', null=True, blank=True)
    city = models.ForeignKey(verbose_name='Город', to=City, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')

    def __str__(self) -> str:
        return f'Заказ №{self.number}'

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = Order.generate_unique_order_number()
        
        if not self.is_discount_applied: 
            if self.percentage_discount: 
                self.total_price -= self.total_price * self.percentage_discount
                self.is_discount_applied = True

        super().save(*args, **kwargs)

    def update_total_price(self) -> None:
        self.total_price = sum(item.total_price for item in self.items.all())
        self.save()

    def create_pdf_bill(self) -> None: 
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                generate_pdf_bill(
                    output_filename=temp_file.name,
                    pdf_title=f"Заказ №{self.number}",
                    items=self.items.all(), 
                    order=self
                )
                
                temp_file.seek(0)
                pdf_content = temp_file.read()
                temp_file_path = temp_file.name
        
            pdf_file_name = f'Заказ_№{self.number}.pdf'
            self.pdf_bill.save(pdf_file_name, ContentFile(pdf_content), save=True)
        finally: 
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    @staticmethod
    def generate_unique_order_number(length=8) -> str:
        characters = string.digits
        while True:
            order_number = ''.join(random.choice(characters) for _ in range(length))
            if not Order.objects.filter(number=order_number).exists():
                return order_number
            


@receiver(post_save, sender=Order)
def after_order_save(sender, instance: Order, created, **kwargs):
    if created:
        responsible_user_email = instance.manager.email 
        responsible_user_id = crm.get_user_id(user_email=responsible_user_email)

        id_in_amocrm = crm.create_lead(
            name = f'Заказ с сайта №{instance.number}',
            responsible_user_id = responsible_user_id, 
            contact_id = instance.user.id_in_amocrm if instance.user else None, 
            price = instance.total_price
        )
        instance.id_in_amocrm = id_in_amocrm 
        instance.save()
    pass


class OrderItem(models.Model):
    product_name = models.CharField('Товар')
    brand_name = models.CharField('Производитель', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('Заказ'))
    quantity = models.PositiveIntegerField(_('Количество'), default=1)
    unit_price = models.DecimalField(_('Цена за единицу'), decimal_places=2, max_digits=14, default=0)
    total_price = models.DecimalField(_('Итоговая цена'), decimal_places=2, max_digits=14, default=0)

    class Meta:
        verbose_name = _('Позиция заказа')
        verbose_name_plural = _('Позиции заказов')

    def __str__(self) -> str:
        return f'Заказ №{self.order.number} | {self.product_name} | {self.unit_price} Р | {self.quantity} шт.'

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        self.order.update_total_price()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.order.update_total_price()


class ImportOrderStatus(models.Model):
    class Type(models.TextChoices):
        INFO = 'INFO', 'Информация'
        PROCESS = 'PROCESS', 'Обработка'
        ERROR = 'ERROR', 'Ошибка'
        SUCCESS = 'SUCCESS', 'Успех'

    text = models.CharField(_('Текст'), max_length=200)
    time = models.TimeField(_('Время'), auto_now_add=True)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('Менеджер'))
    status_type = models.CharField(_('Тип'), max_length=10, choices=Type.choices, default=Type.INFO)

    class Meta:
        verbose_name = _('Статус импорта')
        verbose_name_plural = _('Статус импорта')
        ordering = ['-time']

    def __str__(self) -> str:
        return self.text
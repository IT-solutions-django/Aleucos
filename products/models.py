from django.db import models 
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models.signals import pre_delete, pre_save
from django.dispatch.dispatcher import receiver
import random
from django.utils.translation import gettext_lazy as _
from Aleucos import settings


class Brand(models.Model): 
    title = models.CharField(_('Название'), max_length=60, null=False)
    is_published = models.BooleanField(_('Опубликован'), default=True)

    class Meta: 
        verbose_name = _('Бренд')
        verbose_name_plural = _('Бренды')

    def __str__(self) -> str: 
        return self.title
    

class Category(models.Model): 
    title = models.CharField(_('Название'), max_length=80, null=False, unique=True)

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')

    def __str__(self) -> str: 
        return self.title


class Product(models.Model): 
    barcode = models.BigIntegerField(_('Штрихкод')) 
    brand = models.ForeignKey(Brand, verbose_name=_('Бренд'), on_delete=models.CASCADE, null=False, related_name='products') 
    title = models.CharField(_('Название'), max_length=200, null=False) 
    description = models.CharField(_('Описание'), max_length=200, null=True, blank=True) 
    category = models.ForeignKey(Category, verbose_name=_('Категория'), on_delete=models.CASCADE, null=True, related_name='categories')
    photo = models.ImageField(_('Фото'), upload_to='products', null=False, default=settings.DEFAULT_IMAGE_PATH) 
    volume = models.CharField(_('Объём'), max_length=100, null=True) 
    weight = models.DecimalField(_('Вес'), decimal_places=2, max_digits=4, null=True, blank=True,
                                 validators=(MinValueValidator(Decimal(0), _('Вес не может быть отрицательным')),))
    notes = models.CharField(_('Заметки'), max_length=30, null=True, blank=True)
    price_before_200k = models.DecimalField(_('Цена до 200 тыс'), decimal_places=2, max_digits=8) 
    price_after_200k = models.DecimalField(_('Цена после 200 тыс'), decimal_places=2, max_digits=8) 
    price_after_500k = models.DecimalField(_('Цена после 500 тыс'), decimal_places=2, max_digits=8) 
    is_in_stock = models.BooleanField(_('В наличии'), default=False)
    remains = models.PositiveIntegerField(_('Остаток на складе'), default=0)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    is_frozen = models.BooleanField(_('Зафиксирован'), default=False)

    class Meta: 
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')
        ordering = ['-remains']

    def __str__(self) -> str:
        return f'{self.title}'
    
    def save(self, *args, **kwargs) -> None:
        # Присваиваем случайную категорию
        if self.barcode is None:
            categories = Category.objects.all()
            
            if categories.exists():
                self.category = random.choice(categories)
        
        while_importing_catalog = kwargs.pop('while_importing_catalog', False)

        # TODO: выкинуть это в фоновую задачу
        # if not while_importing_catalog:
        #     from .services import CatalogExcelService
        #     CatalogExcelService.update_or_add_product_in_excel(self)

        super(Product, self).save(*args, **kwargs)


@receiver(pre_save, sender=Product)
def elasticsearch_sync_on_save(sender, instance, **kwargs) -> None: 
    from .documents import ProductDocument

    if settings.ELASTICSEARCH_SYNC: 
        ProductDocument().update(instance)

@receiver(pre_save, sender=Product)
def elasticsearch_sync_on_save(sender, instance, **kwargs) -> None: 
    from .documents import ProductDocument
    
    if settings.ELASTICSEARCH_SYNC: 
        ProductDocument().update(instance)
    

@receiver(pre_delete, sender=Product)
def image_delete(sender, instance, **kwargs):
    if instance.photo.name:
        if instance.photo.name != settings.DEFAULT_IMAGE_PATH:
            instance.photo.delete(False)


class ImportProductsStatus(models.Model): 
    text = models.CharField(_('Текст'), max_length=200, null=False) 
    time = models.TimeField(_('Время'), auto_now_add=True)

    class Meta:
        verbose_name = _('Статус импорта товаров')
        verbose_name_plural = _('Статусы импорта товаров')

    def __str__(self) -> str: 
        return self.text
from django.db import models 
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models.signals import pre_delete, pre_save
from django.dispatch.dispatcher import receiver
import random
from django.utils.translation import gettext_lazy as _
from Aleucos import settings
from users.models import User
from django.utils.text import slugify
from django.urls import reverse


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
    

class ProductType(models.Model): 
    title = models.CharField(_('Название'), max_length=80, null=False, unique=True) 

    class Meta:
        verbose_name = _('Тип продукта')
        verbose_name_plural = _('Типы продукта')

    def __str__(self) -> str: 
        return self.title


class Product(models.Model): 
    article = models.CharField('Артикул', max_length=9)
    barcode = models.BigIntegerField(_('Штрихкод'), null=True, blank=True) 
    brand = models.ForeignKey(Brand, verbose_name=_('Бренд'), on_delete=models.CASCADE, null=True, blank=True, related_name='products') 
    title = models.CharField(_('Название'), max_length=200, null=False) 
    description = models.CharField(_('Описание'), max_length=200, null=True, blank=True) 
    category = models.ForeignKey(Category, verbose_name=_('Категория'), on_delete=models.CASCADE, null=True, blank=True, related_name='categories')
    photo = models.ImageField(_('Фото'), upload_to='products', null=False, default=settings.DEFAULT_IMAGE_PATH) 
    volume = models.CharField(_('Объём'), max_length=100, null=True) 
    weight = models.DecimalField(_('Вес'), decimal_places=2, max_digits=4, null=True, blank=True,
                                 validators=(MinValueValidator(Decimal(0), _('Вес не может быть отрицательным')),))
    notes = models.CharField(_('Заметки'), max_length=30, null=True, blank=True)
    price_before_200k = models.DecimalField(_('Цена до 200 тыс'), decimal_places=6, max_digits=14) 
    price_after_200k = models.DecimalField(_('Цена после 200 тыс'), decimal_places=6, max_digits=14) 
    price_after_500k = models.DecimalField(_('Цена после 500 тыс'), decimal_places=6, max_digits=14) 
    is_in_stock = models.BooleanField(_('В наличии'), default=False)
    remains = models.PositiveIntegerField(_('Остаток на складе'), default=0)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    will_arrive_at = models.DateField(_('Дата поступления (если в пути)'), null=True, blank=True)
    slug = models.SlugField('Слаг', blank=True, max_length=80)
    composition = models.TextField('Состав', max_length=500, null=True, blank=True)
    product_type = models.ForeignKey(verbose_name='Тип продукта', to=ProductType, null=True, blank=True, on_delete=models.SET_NULL)
    is_hit = models.BooleanField('Хит продаж', default=False)

    class Meta: 
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')

    def __str__(self) -> str:
        return f'{self.title}'
    
    def get_absolute_url(self) -> str: 
        return reverse('products:product', args=[self.slug])
    
    def save(self, *args, **kwargs) -> None: 
        from .services import generate_unique_article_number

        if self.remains == 0: 
            self.is_in_stock = False 
        else: 
            self.is_in_stock = True

        if not self.article: 
            self.article = generate_unique_article_number()

        if not self.slug:
            self.slug = f"{str(self.barcode) if self.barcode else ''}-{slugify(self.title[:50])}"

        super(Product, self).save(*args, **kwargs)
    

@receiver(pre_delete, sender=Product)
def image_delete(sender, instance, **kwargs):
    if instance.photo.name:
        if instance.photo.name != settings.DEFAULT_IMAGE_PATH:
            instance.photo.delete(False)


class ImportProductsStatus(models.Model): 
    class Type(models.TextChoices):
        INFO = 'INFO', 'Информация'
        PROCESS = 'PROCESS', 'Обработка'
        ERROR = 'ERROR', 'Ошибка'
        SUCCESS = 'SUCCESS', 'Успех'

    text = models.CharField(_('Текст'), max_length=200, null=False) 
    time = models.DateTimeField(_('Дата и время'), auto_now_add=True)
    status_type = models.CharField(_('Тип'), max_length=10, choices=Type.choices, default=Type.INFO)

    class Meta:
        verbose_name = _('Статус импорта')
        verbose_name_plural = _('Статус импорта')
        ordering = ['-pk']

    def __str__(self) -> str: 
        return self.text
    

class WatermarkConfig(models.Model):
    POSITION_CHOICES = [
        ("top_left", "Слева сверху"),
        ("top_right", "Справа сверху"),
        ("bottom_left", "Слева снизу"),
        ("bottom_right", "Справа снизу"),
        ("center", "По центру"),
    ]
    
    position = models.CharField('Позиция', max_length=20, choices=POSITION_CHOICES, default="bottom_right")
    font_size = models.PositiveIntegerField('Размер шрифта', default=30)
    text = models.CharField('Текст', max_length=255, default="©Aleucos")
    opacity = models.PositiveIntegerField('Прозрачность', default=180, help_text="(0-255)")

    def __str__(self):
        return f"Водяной знак: {self.text},  {self.position}"
    
    def save(self, *args, **kwargs):
        if self.__class__.objects.count():
            self.pk = self.__class__.objects.first().pk
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls) -> "WatermarkConfig":
        instance, created = cls.objects.get_or_create(id=1)
        return instance
    
    class Meta: 
        verbose_name = 'настройки вотермарки'
        verbose_name_plural = 'Вотермарка'
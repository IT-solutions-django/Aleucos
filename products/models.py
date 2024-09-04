from django.db import models 
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models.signals import pre_delete, pre_save
from django.dispatch.dispatcher import receiver
import random
from Aleucos.settings import DEFAULT_IMAGE_PATH


class Brand(models.Model): 
    title = models.CharField(max_length=60, null=False)

    def __str__(self) -> str: 
        return self.title
    

class Category(models.Model): 
    title = models.CharField(max_length=80, null=False, unique=True) 

    def __str__(self) -> str: 
        return self.title


class Product(models.Model): 
    barcode = models.BigIntegerField(primary_key=True) 
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=False, related_name='products') 
    title = models.CharField(max_length=200, null=False) 
    description = models.CharField(max_length=200, null=True, blank=True) 
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name='categories')
    photo = models.ImageField(upload_to='products', null=False) 
    volume = models.CharField(max_length=100, null=True) 
    weight = models.DecimalField(decimal_places=2, max_digits=4, null=True, blank=True,
                                 validators=(MinValueValidator(Decimal(0), 'Weight cannot be negative'),))
    notes = models.CharField(max_length=30, null=True, blank=True)
    price_before_200k = models.DecimalField(decimal_places=2, max_digits=8) 
    price_after_200k = models.DecimalField(decimal_places=2, max_digits=8) 
    price_after_500k = models.DecimalField(decimal_places=2, max_digits=8) 
    is_in_stock = models.BooleanField(default=False)
    remains = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now_add=True )

    class Meta: 
        ordering = ['-barcode']

    def __str__(self) -> str:
        return f'{self.brand} | {self.title}'
    
    def save(self, *args, **kwargs) -> None:
        if self.barcode is None:
            categories = Category.objects.all()
            
            if categories.exists():
                self.category = random.choice(categories)
        
        super(Product, self).save(*args, **kwargs)
    


@receiver(pre_delete, sender=Product)
def image_delete(sender, instance, **kwargs):
    if instance.photo.name:
        if instance.photo.name != DEFAULT_IMAGE_PATH:
            instance.photo.delete(False)


class ImportStatus(models.Model): 
    text = models.CharField(max_length=200, null=False) 
    time = models.TimeField(auto_now_add=True)

    def __str__(self) -> str: 
        return self.text
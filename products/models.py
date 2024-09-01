from django.db import models 
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver


class Brand(models.Model): 
    title = models.CharField(max_length=60, null=False)

    def __str__(self) -> str: 
        return self.title


class Product(models.Model): 
    barcode = models.BigIntegerField(primary_key=True) 
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=False, related_name='products') 
    title = models.CharField(max_length=200, null=False) 
    description = models.CharField(max_length=200, null=True, blank=True) 
    photo = models.ImageField(upload_to='products', null=False) 
    volume = models.CharField(max_length=100, null=True) 
    weight = models.DecimalField(decimal_places=2, max_digits=4, null=True, blank=True,
                                 validators=(MinValueValidator(Decimal(0), 'Weight cannot be negative'),))
    notes = models.CharField(max_length=30, null=True, blank=True)
    price_before_200k = models.DecimalField(decimal_places=2, max_digits=8) 
    price_after_200k = models.DecimalField(decimal_places=2, max_digits=8) 
    price_after_500k = models.DecimalField(decimal_places=2, max_digits=8) 
    amount = models.PositiveIntegerField(default=0)
    is_in_stock = models.BooleanField(default=False)
    remains = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'{self.brand} | {self.title}'
    


@receiver(pre_delete, sender=Product)
def image_model_delete(sender, instance, **kwargs):
    if instance.photo.name:
        instance.photo.delete(False)
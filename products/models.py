from django.db import models 
from django.core.validators import MinValueValidator
from decimal import Decimal


class Brand(models.Model): 
    title = models.CharField(max_length=40, null=False)


class Product(models.Model): 
    barcode = models.BigIntegerField(primary_key=True) 
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=False, related_name='products') 
    title = models.CharField(max_length=150, null=False) 
    description = models.CharField(max_length=150, null=False) 
    photo = models.ImageField(upload_to='products', null=False) 
    volume = models.CharField(max_length=20) 
    weight = models.DecimalField(decimal_places=2, max_digits=4, 
                                 validators=(MinValueValidator(Decimal(0), 'Weight cannot be negative'),))
    notes = models.CharField(max_length=30)
    price_before_200k = models.DecimalField(decimal_places=2, max_digits=8) 
    price_after_200k = models.DecimalField(decimal_places=2, max_digits=8) 
    price_after_500k = models.DecimalField(decimal_places=2, max_digits=8) 
    amount = models.PositiveIntegerField(default=0)
    remains = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'{self.brand} | {self.title}'
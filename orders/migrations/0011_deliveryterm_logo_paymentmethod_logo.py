# Generated by Django 5.1 on 2025-03-10 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_order_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryterm',
            name='logo',
            field=models.FileField(blank=True, null=True, upload_to='orders/delivery_terms/', verbose_name='Логотип'),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='logo',
            field=models.FileField(blank=True, null=True, upload_to='orders/payment_methods/', verbose_name='Логотип'),
        ),
    ]

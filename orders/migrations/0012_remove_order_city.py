# Generated by Django 5.1 on 2025-03-10 23:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_deliveryterm_logo_paymentmethod_logo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='city',
        ),
    ]

# Generated by Django 5.1 on 2024-11-02 05:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_product_price_after_200k_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='is_frozen',
        ),
    ]

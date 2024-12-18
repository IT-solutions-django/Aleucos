# Generated by Django 5.1 on 2024-09-24 10:15

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryTerm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Условие доставки',
                'verbose_name_plural': 'Условия доставки',
            },
        ),
        migrations.CreateModel(
            name='ImportOrderStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=200, verbose_name='Текст')),
                ('time', models.TimeField(auto_now_add=True, verbose_name='Время')),
            ],
            options={
                'verbose_name': 'Статус импорта заказа',
                'verbose_name_plural': 'Статусы импорта заказов',
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Количество')),
                ('unit_price', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Цена за единицу')),
                ('total_price', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Итоговая цена')),
            ],
            options={
                'verbose_name': 'Позиция заказа',
                'verbose_name_plural': 'Позиции заказов',
            },
        ),
        migrations.CreateModel(
            name='OrderStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Статус',
                'verbose_name_plural': 'Статусы',
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Способ оплаты',
                'verbose_name_plural': 'Способы оплаты',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=16, verbose_name='Номер заказа')),
                ('total_price', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Итоговая цена')),
                ('percentage_discount', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Процент скидки')),
                ('is_discount_applied', models.BooleanField(default=False, verbose_name='Скидка применена')),
                ('is_paid', models.BooleanField(default=False, verbose_name='Оплачено')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Комментарий')),
                ('delivery_terms', models.ForeignKey(default=0, on_delete=django.db.models.deletion.SET_DEFAULT, to='orders.deliveryterm', verbose_name='Условия доставки')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': 'Заказы',
            },
        ),
    ]

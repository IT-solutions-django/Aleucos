# Generated by Django 5.1 on 2024-11-20 07:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_alter_order_user'),
        ('users', '0013_registrationrequest_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='city',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.city', verbose_name='Город'),
            preserve_default=False,
        ),
    ]

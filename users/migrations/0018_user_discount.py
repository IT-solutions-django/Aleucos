# Generated by Django 5.1 on 2025-04-08 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_user_comments_user_legal_entity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='discount',
            field=models.IntegerField(blank=True, choices=[(5, '5%'), (10, '10%'), (15, '15%')], null=True, verbose_name='Скидка'),
        ),
    ]

# Generated by Django 5.1 on 2024-11-13 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_registrationrequest_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='id_in_amocrm',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID в amoCRM'),
        ),
    ]
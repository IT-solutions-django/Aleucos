# Generated by Django 5.1 on 2024-10-31 10:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('configs', '0002_rename_settings_configs'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Configs',
            new_name='Config',
        ),
    ]

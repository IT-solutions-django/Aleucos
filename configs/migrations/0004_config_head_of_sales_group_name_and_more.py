# Generated by Django 5.1 on 2024-11-08 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configs', '0003_rename_configs_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='config',
            name='head_of_sales_group_name',
            field=models.CharField(default='РОП', help_text='Название группы для РОПа', verbose_name='HEAD_OF_SALES_GROUP_NAME'),
        ),
        migrations.AlterField(
            model_name='config',
            name='admins_group_name',
            field=models.CharField(default='Администраторы', help_text='Название группы для администраторов', verbose_name='ADMINS_GROUP_NAME'),
        ),
        migrations.AlterField(
            model_name='config',
            name='managers_group_name',
            field=models.CharField(default='Менеджеры', help_text='Название группы для менеджеров', verbose_name='MANAGERS_GROUP_NAME'),
        ),
        migrations.AlterField(
            model_name='config',
            name='users_group_name',
            field=models.CharField(default='Клиенты', help_text='Название группы для зарегистрированных пользователей', verbose_name='USERS_GROUP_NAME'),
        ),
    ]
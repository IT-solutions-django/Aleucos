# Generated by Django 5.1 on 2025-03-02 23:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0017_alter_watermarkconfig_opacity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='watermarkconfig',
            name='position',
            field=models.CharField(choices=[('top_left', 'Слева сверху'), ('top_right', 'Справа сверху'), ('bottom_left', 'Слева снизу'), ('bottom_right', 'Справа снизу'), ('center', 'По центру')], default='bottom_right', max_length=20),
        ),
    ]

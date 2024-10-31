from django.db import models


def get_default_order_status_name_mapper():
    return {
        'Первичный контакт': 'В обработке',
        'Рабочий контакт': 'В обработке',
        'КП отправлено': 'В обработке',
        'Клиент прислал заказ': 'В обработке',
        'Товар собран': 'Комплектация заказа',
        'Оплата получена': 'Оплата получена',
        'Отгружено в рассрочку': 'Транспортировка',
        'Товар отправлен/передан': 'Транспортировка',
        'Успешно реализовано': 'Заказ принят',
    }


class Settings(models.Model): 
    import_catalog_filename = models.CharField(
        'IMPORT_CATALOG_FILENAME', 
        max_length=150, 
        help_text='Название, под которым сохраняется Excel-файл с каталогом при импорте', 
        default='catalog.xlsx'
    )
    export_catalog_filename = models.CharField(
        'EXPORT_CATALOG_FILENAME', 
        max_length=150, 
        help_text='Название Excel-файла с экспортированным каталогом', 
        default='catalog_for_export.xlsx'
    )
    export_catalog_template_filename = models.CharField(
        'EXPORT_CATALOG_TEMPLATE_FILENAME', 
        max_length=150, 
        help_text='Название Excel-файла-шаблона для экспорта каталога', 
        default='catalog_template.xlsx'
    )

    order_status_name_mapper = models.JSONField(
        'ORDER_STATUS_NAME_CONVERTER', 
        help_text='JSON для соответствия статусов сделок и заказов. { статус_сделки: статус_заказа, ... }',
        default=get_default_order_status_name_mapper
    )
    order_status_first = models.CharField(
        'ORDER_STATUS_FIRST', 
        help_text='Первый статус заказа в базе данных', 
        default='В обработке'
    )
    lead_status_first = models.CharField(
        'LEAD_STATUS_FIRST', 
        help_text='Первый статус сделки, с которого начинается путь заказа', 
        default='Клиент прислал заказ'
    )
    lead_status_last = models.CharField(
        'LEAD_STATUS_LAST', 
        help_text='Последний статус сделки', 
        default='Успешно реализовано'
    )

    admins_group_name = models.CharField(
        'ADMINS_GROUP_NAME', 
        help_text='Название группы для администраторов', 
        default='Administrators'
    )
    managers_group_name = models.CharField(
        'MANAGERS_GROUP_NAME', 
        help_text='Название группы для менеджеров', 
        default='Managers'
    )
    users_group_name = models.CharField(
        'USERS_GROUP_NAME', 
        help_text='Название группы для зарегистрированных пользователей', 
        default='Users'
    )

    class Meta:
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"



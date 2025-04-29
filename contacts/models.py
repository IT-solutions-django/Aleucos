from django.db import models


class CompanyInfo(models.Model): 
    whatsapp_link = models.URLField('Ссылка на WhatsApp', max_length=200, null=True, blank=True)
    telegram_link = models.URLField('Ссылка на Telegram', max_length=200, null=True, blank=True)
    phone = models.CharField('Номер телефона', max_length=20, null=True, blank=True)

    inn = models.CharField('ИНН', max_length=12, default='5402068150')
    kpp = models.CharField('КПП', max_length=20, default='1215400031714')
    ogrn = models.CharField('ОГРН', max_length=13, default='1215400031714')
    registration_date = models.DateField('Дата регистрации', default='2021-07-26')
    authorized_capital = models.CharField('Уставный капитал', max_length=50, default='10 000 руб.')
    address = models.CharField('Адрес', max_length=200, default='г.Владивосток, ул. Днепровская, д.25д, стр.4а')
    legal_address = models.TextField('Юридический адрес', default='630001, Новосибирская область, г Новосибирск, Владимировская ул, зд. 26/1, этаж 5 офис 504')

    class Meta: 
        verbose_name = 'Информация о компании'
        verbose_name_plural = 'Информация о компании'

    def __str__(self):
        return 'Информация о компании'
    
    def save(self, *args, **kwargs):
        if self.__class__.objects.count():
            self.pk = self.__class__.objects.first().pk
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls) -> "CompanyInfo":
        instance, created = cls.objects.get_or_create(id=1)
        return instance
    

class ContactsManager(models.Model):
    name = models.CharField('Имя', max_length=100) 
    phone = models.CharField('Телефон', max_length=18) 
    email = models.EmailField('Email', max_length=80) 
    photo = models.ImageField('Фото', upload_to='contacts/managers/')

    def __str__(self):
        return f'{self.name}'
        
    class Meta: 
        verbose_name = 'Менеджер'
        verbose_name_plural = 'Менеджеры'


class Partner(models.Model): 
    name = models.CharField('Название', max_length=100) 
    logo = models.FileField('Логотип', upload_to='contacts/partners/')

    def __str__(self):
        return f'{self.name}' 
    
    class Meta: 
        verbose_name = 'Партнёр'
        verbose_name_plural = 'Партнёры'
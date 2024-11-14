from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from .services import generate_random_password
from Aleucos.crm import crm
from .tasks import send_email_to_new_user_task
from configs.models import Config


class Position(models.Model):
    title = models.CharField(_('Название'), max_length=40, null=False)

    class Meta:
        verbose_name = _('Должность')
        verbose_name_plural = _('Должности')

    def __str__(self) -> str:
        return self.title


class User(AbstractUser):
    phone = models.CharField(_('Телефон'), max_length=20)
    last_name = models.CharField(_('Фамилия'), max_length=50)
    first_name = models.CharField(_('Имя'), max_length=50)
    patronymic = models.CharField(_('Отчество'), max_length=50, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Должность'))
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='customers', verbose_name=_('Менеджер'))
    email = models.EmailField(_('Электронная почта'), unique=True)
    password = models.CharField(_('Пароль'), max_length=128, blank=True)
    photo = models.ImageField(_('Фотография'), upload_to='users', null=True, blank=True)

    instagram = models.URLField(_('Instagram'), null=True, blank=True)
    vk = models.URLField(_('VK'), null=True, blank=True)
    telegram = models.URLField(_('Telegram'), null=True, blank=True)
    work_start_date = models.DateField(_('Дата начала работы'), null=True, blank=True)
    active_orders_count = models.PositiveIntegerField(_('Число активных заказов'), default=0)
    id_in_amocrm = models.IntegerField('ID в amoCRM', null=True, blank=True)


    username = models.CharField(_('Имя пользователя'), max_length=30, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'username']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self):
        return self.email

    def get_fullname(self) -> str:
        return f'{self.last_name} {self.first_name} {self.patronymic if self.patronymic else ""}'.rstrip()


# Для разделения интерфейса в админке 
class UserProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

# @receiver(post_save, sender=UserProxy)
# def after_user_save(sender, instance: UserProxy, created, **kwargs):
#     if created and instance.is_active:
#         responsible_user_email = instance.manager.email
#         responsible_user_id = crm.get_user_id(responsible_user_email) 

#         id_in_amocrm = crm.create_contact(
#             name = instance.get_fullname(), 
#             responsible_user_id = responsible_user_id, 
#             email = instance.email, 
#             phone = instance.phone
#         )
#         instance.id_in_amocrm = id_in_amocrm
#         instance.save()


class StaffProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники' 


class RegistrationRequest(models.Model): 
    last_name = models.CharField(_('Фамилия'), max_length=50)
    first_name = models.CharField(_('Имя'), max_length=50)
    patronymic = models.CharField(_('Отчество'), max_length=50, null=True, blank=True)
    phone = models.CharField(_('Телефон'), max_length=20)
    email = models.EmailField(_('Электронная почта'), unique=True) 
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    manager = models.ForeignKey(User, verbose_name=_('Менеджер'), on_delete=models.CASCADE, null=True, blank=True)
    to_save = models.BooleanField(_('Зарегистрировать?'), default=False)

    class Meta:
        verbose_name = _('Заявка')
        verbose_name_plural = _('Заявки')
        ordering = ['-created_at']

    def __str__(self) -> str: 
        return self.email


@receiver(pre_save, sender=RegistrationRequest)
def before_request_save(sender, instance, **kwargs):
    if instance.pk:  
        try:
            old_instance = RegistrationRequest.objects.get(pk=instance.pk)
            instance._old_manager = old_instance.manager
        except RegistrationRequest.DoesNotExist:
            instance._old_manager = None

@receiver(post_save, sender=RegistrationRequest)
def after_request_save(sender, instance: RegistrationRequest, created, **kwargs):

    if not created and hasattr(instance, '_old_manager'):
        if instance._old_manager != instance.manager and instance._old_manager == None:
            responsible_user_email = instance.manager.email 
            responsible_user_id = crm.get_user_id(responsible_user_email)
            crm.create_task(
                text = f'Обработать заявку от {instance.email} на сайте', 
                responsible_user_id=responsible_user_id
            )

        if instance.to_save: 
            new_user: User = User.objects.create(
                email=instance.email, 
                phone=instance.phone, 
                last_name=instance.last_name, 
                first_name=instance.first_name, 
                patronymic=instance.patronymic, 
                manager=instance.manager, 
            )
            raw_password = generate_random_password()
            new_user.set_password(raw_password)
            new_user.save()

            new_user.groups.add(Group.objects.get(name=Config.get_instance().users_group_name))
            new_user.save()

            send_email_to_new_user_task.delay(new_user.email, raw_password)

            responsible_user_email = instance.manager.email 
            responsible_user_id = crm.get_user_id(responsible_user_email)
            id_in_amocrm = crm.create_contact(
                name = new_user.get_fullname(), 
                responsible_user_id=responsible_user_id, 
                email = new_user.email, 
                phone = new_user.phone
            )
            new_user.id_in_amocrm = id_in_amocrm 
            new_user.save()


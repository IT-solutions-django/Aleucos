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
    first_name = models.CharField(_('Имя'), max_length=50)
    last_name = models.CharField(_('Фамилия'), max_length=50)
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


def set_password_and_mail_if_needed(user: User):
    try:
        users_group = Group.objects.get(name=Config.get_instance().users_group_name)
        if users_group in user.groups.all():
            raw_password = generate_random_password()

            send_email_to_new_user_task.delay(user.pk, user.email, raw_password)

            user.set_password(raw_password)

        user.save(update_fields=['password'])
    except Group.DoesNotExist:
        pass


# Для разделения интерфейса в админке 
class UserProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

@receiver(post_save, sender=UserProxy)
def after_user_save(sender, instance, created, **kwargs):
    if created and instance.is_active:
        transaction.on_commit(lambda: set_password_and_mail_if_needed(instance))

        crm.create_new_user(instance)


class StaffProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники' 


class RegistrationRequest(models.Model): 
    first_name = models.CharField(_('Имя'), max_length=50)
    last_name = models.CharField(_('Фамилия'), max_length=50)
    patronymic = models.CharField(_('Отчество'), max_length=50, null=True, blank=True)
    phone = models.CharField(_('Телефон'), max_length=20)
    email = models.EmailField(_('Электронная почта'), unique=True) 
    manager = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = _('Заявка')
        verbose_name_plural = _('Заявки')


@receiver(pre_save, sender=RegistrationRequest)
def before_user_save(sender, instance, **kwargs):
    if instance.pk:  
        try:
            old_instance = RegistrationRequest.objects.get(pk=instance.pk)
            instance._old_manager = old_instance.manager
        except RegistrationRequest.DoesNotExist:
            instance._old_manager = None

@receiver(post_save, sender=RegistrationRequest)
def after_user_save(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_old_manager'):
        if instance._old_manager != instance.manager and instance._old_manager == None:
            crm.create_new_task_for_client_registration(instance)
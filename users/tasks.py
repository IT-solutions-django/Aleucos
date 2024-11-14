from celery import shared_task 
from .services import send_email_to_new_user


@shared_task
def send_email_to_new_user_task(login: str, raw_password: str) -> None:
    print('отправляем письмо')
    send_email_to_new_user(login, raw_password)
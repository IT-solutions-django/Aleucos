from celery import shared_task 
from .services import send_email_to_new_user


@shared_task
def send_email_to_new_user_task(user_id: int, login: str, raw_password: str) -> None:
    send_email_to_new_user(user_id, login, raw_password)
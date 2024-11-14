from celery import shared_task 
from .services import (
    send_email_to_new_user, 
    send_email_when_new_status,
)


@shared_task
def send_email_to_new_user_task(login: str, raw_password: str) -> None:
    send_email_to_new_user(login, raw_password)


@shared_task
def send_email_when_new_status_task(email: str, order_number: str, new_status: str) -> None: 
    send_email_when_new_status(
        email=email, 
        order_number=order_number, 
        new_status=new_status
    )
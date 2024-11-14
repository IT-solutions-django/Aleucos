import random
import string
from django.core.mail import EmailMessage
from django.conf import settings


def generate_random_password(length=10):
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def send_email_to_new_user(login: str, raw_password: str) -> None: 
    subject = 'Вход в аккаунт'
    message = f'Логин: {login}\nПароль: {raw_password}'
    
    email = EmailMessage(subject=subject,
                        body=message, 
                        to=(login,))
    email.send()


def send_email_when_new_status(email: str, order_number: str, new_status: str) -> None: 
    subject = 'У заказа обновился статус'
    message = f'У вашего заказа №{order_number} обновился статус: {new_status}'
    
    email = EmailMessage(subject=subject,
                        body=message, 
                        to=(email,))
    email.send()
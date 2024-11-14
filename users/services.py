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
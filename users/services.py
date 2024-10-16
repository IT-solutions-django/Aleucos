import random
import string
from django.core.mail import EmailMessage
from django.conf import settings


def generate_random_password(length=10):
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def send_email_to_new_user(user_id: int, login: str, raw_password: str) -> None: 
    from users.models import User

    try:
        subject = 'Вход в аккаунт'
        message = f'Логин: {login}\nПароль: {raw_password}'
        
        email = EmailMessage(subject=subject,
                            body=message, 
                            to=(User.objects.get(pk=user_id).email,))
        email.send()
    except User.DoesNotExist: 
        pass
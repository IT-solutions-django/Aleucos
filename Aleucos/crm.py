from decimal import Decimal
import os
import datetime, time
import dotenv
from loguru import logger
from Aleucos import settings
from configs.models import Config
import requests


dotenv.load_dotenv()

class AmoCRM: 
    def __init__(self, subdomain: str, client_id: str, client_secret: str, redirect_uri: str): 
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.REDIRECT_URI = redirect_uri
        self.SUBDOMAIN = subdomain
        self.CLIENT_DOMAIN = f'https://{self.SUBDOMAIN}.amocrm.ru/'

        self.access_token_path = os.path.join(settings.BASE_DIR, 'amocrm_tokens', 'access_token.txt')
        self.refresh_token_path = os.path.join(settings.BASE_DIR, 'amocrm_tokens', 'refresh_token.txt')

    def get_initial_tokens(self, authorization_code: str) -> None: 
        url = f'{self.CLIENT_DOMAIN}oauth2/access_token'
        data = {
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.REDIRECT_URI
        }
        response = requests.post(url, data=data)

        if response.status_code == 200: 
            access_token = response.json()['access_token']
            refresh_token = response.json()['refresh_token']

            logger.info(f'Acess token получен')
            logger.info(f'Refresh token получен')

            with open(self.access_token_path, 'w', encoding='utf-8') as file: 
                file.write(access_token)
            with open(self.refresh_token_path, 'w', encoding='utf-8') as file: 
                file.write(refresh_token)
        else: 
            logger.error(f'Ошибка получения токенов. Код {response.status_code}') 
            print(response.json())

    def refresh_tokens(self, ) -> None: 
        url = f'{self.CLIENT_DOMAIN}oauth2/access_token'
        data = {
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': self.get_current_refresh_token(),
            'redirect_uri': self.REDIRECT_URI
        }
        response = requests.post(url, data=data)

        if response.status_code == 200: 
            access_token = response.json()['access_token']
            refresh_token = response.json()['refresh_token']

            logger.info(f'Access token обновлён')
            logger.info(f'Refresh token обновлён')

            with open(self.access_token_path, 'w', encoding='utf-8') as file: 
                file.write(access_token)
            with open(self.refresh_token_path, 'w', encoding='utf-8') as file: 
                file.write(refresh_token)
        else: 
            logger.error(f'Ошибка обновления токенов. Код {response.status_code}\n{response.text}') 

    def create_lead(
            self, 
            name: str, 
            responsible_user_id: int, 
            contact_id: int = None,
            price: float = None, 
            from_the_very_first_status: bool = False
        ) -> int: 
        url = f'{self.CLIENT_DOMAIN}api/v4/leads'
        data = [{
            'name': name,
            'created_by': 0, 
            'status_id': 59520526 if not from_the_very_first_status else 59520514
        }]
        (lead_data,) = data
        lead_data['responsible_user_id'] = responsible_user_id
        if price: 
            lead_data['price'] = self._round_price_to_int(price)
        if contact_id:
            lead_data.setdefault('_embedded', {}).setdefault('contacts', []).append({'id': contact_id})

        headers = {
            'Authorization': f'Bearer {self.get_current_access_token()}'
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200: 
            logger.info(f'Сделка "{name}" создана!')
            return response.json()['_embedded']['leads'][0]['id']
        else: 
            logger.error(f'Ошибка создания сделки. Код {response.status_code}\n{response.text}') 

    def create_contact(  
            self, 
            name: str, 
            responsible_user_id: int, 
            email: str, 
            phone: str
        ) -> int: 
        url = f'{self.CLIENT_DOMAIN}api/v4/contacts'  
        data = [{
            'name': name if name else 'Клиент',
            'responsible_user_id': responsible_user_id, 
            'custom_fields_values': [
                {
                    'field_id': 2504353,
                    'values': [
                        {
                            "value": phone, 
                            "enum_code": "WORK"
                        }
                    ]
                }, 
                {
                    'field_id': 2504355, 
                    'values': [
                        {
                            "value": email, 
                            "enum_code": "WORK"
                        }
                    ]
                }
            ]
        }]
        (contact_data,) = data
        headers = {
            'Authorization': f'Bearer {self.get_current_access_token()}'
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            logger.info(f'Контакт {email} создан!') 
            return response.json()['_embedded']['contacts'][0]['id']
        else: 
            logger.error(f'Ошибка создания контакта. Код {response.status_code}\n{response.text}') 

    def create_task(self, text: str, responsible_user_id: int) -> None: 
        url = f'{self.CLIENT_DOMAIN}api/v4/tasks'
        data = [{
            'text': text,
            'responsible_user_id': responsible_user_id, 
            'complete_till': int(time.time()) + 60 * 60 * 24
        }]
        headers = {
            'Authorization': f'Bearer {self.get_current_access_token()}'
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200: 
            logger.info(f'Задача {text} создана!')
        else: 
            logger.error(f'Ошибка создания задачи. Код {response.status_code}\n{response.text}') 

    def update_lead_data(self, order_id_in_amocrm: int, new_order_status: str = None, price: int = None) -> None: 
        url = f'{self.CLIENT_DOMAIN}api/v4/leads/{order_id_in_amocrm}'
        new_status_id = None
        if new_order_status:
            match new_order_status: 
                case 'Клиент прислал заказ': 
                    new_status_id = 59520526
                case 'Товар собран': 
                    new_status_id = 59948062 
                case 'Оплата получена': 
                    new_status_id = 59948090 
                case 'Отгружено в рассрочку': 
                    new_status_id = 65971030 
                case 'Товар отправлен/передан': 
                    new_status_id = 59948134 

                case 'Первичный контакт': 
                    new_status_id = 59520514 
                case 'Рабочий контакт': 
                    new_status_id = 60739018 
                case 'КП отправлено': 
                    new_status_id = 59520518 
                case _: 
                    raise Exception(f'Такого статуса в amoCRM нет: {new_order_status}')
        headers = {
            'Authorization': f'Bearer {self.get_current_access_token()}'
        }
        data = {}
        if new_order_status:
            data['status_id'] = new_status_id  
        if price: 
            data['price'] = price  
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code == 200: 
            logger.info(f'Задача с id_in_amocrm={order_id_in_amocrm} обновлена, статус={new_order_status}, цена={price}!')
        else: 
            logger.error(f'Ошибка обновления данных задачи с id_in_amocrm={order_id_in_amocrm}. Код {response.status_code}\n{response.text}') 

    def get_user_id(self, user_email: str) -> int: 
        url = f'{self.CLIENT_DOMAIN}api/v4/users'
        headers = {
            'Authorization': f'Bearer {self.get_current_access_token()}'
        }
        print(headers)
        response = requests.get(url, headers=headers)
        print(response.json())

        user_id = None
        for user in response.json()['_embedded']['users']: 
            if user['email'] == user_email: 
                user_id = user['id']

        if user_id is None: 
            raise Exception('Такого менеджера нет в amoCRM')
        return user_id
    
    def get_lead_and_status(self, lead_id: int) -> tuple[str, str]: 
        url = f'{self.CLIENT_DOMAIN}api/v4/leads/{lead_id}'
        headers = {
            'Authorization': f'Bearer {self.get_current_access_token()}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200: 
            lead_name = response.json()['name']
            pipeline_id = response.json()['pipeline_id']
            status_id = response.json()['status_id']

            status_name = self.get_status_name(
                pipeline_id = pipeline_id,
                status_id = status_id
            )

            return (lead_name, status_name)

        else: 
            logger.error(f'Ошибка получения сделки по ID ({lead_id}). Код {response.status_code}\n{response.text}') 

    def get_status_name(self, pipeline_id: int, status_id: int) -> str: 
        url = f'{self.CLIENT_DOMAIN}api/v4/leads/pipelines/{pipeline_id}/statuses/{status_id}'
        headers = {
            'Authorization': f'Bearer {self.get_current_access_token()}'
        }
        response = requests.get(url, headers=headers) 
        if response.status_code == 200: 
            status_name = response.json()['name']
            return status_name
        else: 
            logger.error(f'Ошибка получения статуса по ID ({status_id}). Код {response.status_code}\n{response.text}') 

    def get_user_email(self, user_id: int) -> str: 
        url = f'{self.CLIENT_DOMAIN}api/v4/users/{user_id}'
        headers = {
            'Authorization': f'Bearer {self.get_current_access_token()}'
        }
        response = requests.get(url, headers=headers)  
        if response.status_code == 200: 
            user_email = response.json()['email']
            return user_email
        else: 
            logger.error(f'Ошибка получения пользователя в amoCRM по ID ({user_id}). Код {response.status_code}\n{response.text}') 

    def get_current_access_token(self) -> str | None: 
        with open(self.access_token_path, 'r', encoding='utf-8') as file: 
            access_token = file.read() 
        return access_token
    
    def get_current_refresh_token(self) -> str | None: 
        with open(self.refresh_token_path, 'r', encoding='utf-8') as file: 
            refresh_token = file.read() 
        return refresh_token

    @staticmethod
    def _round_price_to_int(price: Decimal | float) -> int: 
        return int(round(price))


crm = AmoCRM(
    subdomain=os.getenv('AMOCRM_SUBDOMAIN'), 
    client_id=os.getenv('AMOCRM_CLIENT_ID'), 
    client_secret=os.getenv('AMOCRM_CLIENT_SECRET'), 
    redirect_uri=os.getenv('AMOCRM_REDIRECT_URL')
)
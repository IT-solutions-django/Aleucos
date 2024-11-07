from decimal import Decimal
import os
import datetime, time
from amocrm.v2 import Lead, Contact as _Contact, User as _User, custom_field, tokens, fields, Pipeline, Status, Task
from amocrm.v2.fields import _DateTimeField
from loguru import logger
from Aleucos import settings
from configs.models import Config


class Contact(_Contact):
    email = custom_field.ContactEmailField('Email')
    phone = custom_field.ContactPhoneField('Телефон')
    manager = fields._EmbeddedLinkField('managers', 'User')

class User(_User): 
    phone = custom_field.ContactPhoneField('Телефон')


class AmoCRM:
    def __init__(self):
        self.token_storage_path = os.path.join(os.path.dirname(__file__), 'amocrm_tokens')
        os.makedirs(self.token_storage_path, exist_ok=True)

        tokens.default_token_manager(
            client_id=os.getenv('AMOCRM_CLIENT_ID'),
            client_secret=os.getenv('AMOCRM_CLIENT_SECRET'),
            subdomain=os.getenv('AMOCRM_SUBDOMAIN'),
            redirect_url=os.getenv('AMOCRM_REDIRECT_URL'),
            storage=tokens.FileTokensStorage(self.token_storage_path),
        )
        if not tokens.default_token_manager._storage.get_access_token(): 
            code = ''  # Присвоить значение при деплое
            tokens.default_token_manager.init(code=code)
        self.pipeline = list(Pipeline.objects.all())[0] 

    def get_lead_by_id(self, id: int) -> Lead: 
        return Lead.objects.get(object_id=id)        

    def get_user_by_id(self, id: int) -> User: 
        return User.objects.get(object_id=id)    

    def create_new_user(self, user) -> None: 
        manager = user.manager
        try:
            responsible_user = User.objects.get(query=manager.email) 
        except: 
            logger.error(f'Менеджера {manager.get_fullname()} в amoCRM нет')
            return 

        new_contact = Contact(
            name=user.get_fullname(), 
            email=user.email, 
            responsible_user=responsible_user, 
            phone=user.phone
        )

        new_contact.save()

    def create_new_lead(self, order) -> None: 
        manager = order.user.manager
        user = order.user
        
        try:
            responsible_user = User.objects.get(query=manager.email) 
        except: 
            logger.error(f'Менеджера {manager.email} в amoCRM нет')
            return 

        new_lead = Lead(
            name=order.number,
            responsible_user=responsible_user, 
            price=AmoCRM._round_price_to_int(order.total_price),
            pipeline=self.pipeline
        )

        new_lead.status = Status.get_for(self.pipeline).get(query=Config.get_instance().lead_status_first).id
        new_lead.save()
        order.id_in_amocrm = new_lead.id
        order.save()

        try:
            contact = Contact.objects.get(query=user.get_fullname())
        except Exception: 
            logger.error(f'Пользователя {user.get_fullname()} в amoCRM нет')
            return 
        new_lead.contacts.append(contact)

    def create_new_task_for_client_registration(self, registration_request): 
        new_task = Task.objects.create(
            text=f'Заявка с сайта | {registration_request.email}',  
            complete_till=int(time.mktime(datetime.datetime.now().timetuple())) + 60 * 60 * 24, 
        )

    @staticmethod
    def _round_price_to_int(price: Decimal | float) -> int: 
        return int(round(price))

print(os.getenv('AMOCRM_AUTHORIZATION_CODE'))
crm = AmoCRM()
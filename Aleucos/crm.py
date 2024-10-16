from decimal import Decimal
import os
import datetime, time
from amocrm.v2 import Lead, Contact as _Contact, User as _User, custom_field, tokens, fields, Pipeline, Status, Task
from amocrm.v2.fields import _DateTimeField
from loguru import logger
from Aleucos import settings


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
        # tokens.default_token_manager.init(code="def5020047db021d41ee3ec8fd8b27ebbfc93365bf6e28d519b83e6c6cd3fa1828ca781acee98cc4be6c0b250a3bac13ca2bdc4602d4374e7ad9f833023d77a9ac2895c614d58aa9a0a1ad9acb5e5b4e801faed10c8829c0eac7657ce3b64f2edb5c0211aee96306531ec8c03f3329230e6bc406d8880ade6f4a8c10246db855db37d8aa5e1e67cb97b0f38cc72f6399af8729771bd4e12a86b87b1eac89903870fe1a9fb1e71c0a3b84c289965740725fca90faadf08ea9e145a06e8d0f2a740d6da011130ee1744d79f46b91edebef20275b59f9f2ae24e17acecdd3bbc7932e78d346000069c0604e0aa28341d98203e2f4b2769c540c089e7118aa74c559f2ea47f764d2b02dade09329194c4a43ae71745ebb33b68a29bbab247d3941bb7a763e5bf99c017d5c301260bdd6b3c74cc0832a5bfbd3c4c67912d413707ef2e57e3e12e0c2b336fa9a40feeee2961deb3430fecf38e5c7a3f3f0cfa6fe3c06d52e5dc2ce1dd33cfcb77b7224c9df852590535ddbf27027c492ccd0b4164377cd6d8c38e5b192eeb06a4aa2b52e58697a6c05606eeecef210dba82864b4f87724f603c0bbc7daf31a2be29a18dfa467bd60fbbe6e861a675e0eacc48bb933b967c0076dcd760dcc546e47176cc4cbf893864968fd638bff533368cb38e9bfa3")
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

        new_lead.status = Status.get_for(self.pipeline).get(query=settings.LEAD_STATUS_FIRST).id

        new_lead.save()
        order.id_in_amocrm = new_lead.id

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


crm = AmoCRM()
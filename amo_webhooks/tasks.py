from celery import shared_task 
from Aleucos.crm import tokens
from loguru import logger


@shared_task
def refresh_tokens_task() -> None:
    new_access_token, new_refresh_token = tokens.default_token_manager._get_new_tokens()
    tokens.default_token_manager._storage.save_tokens(new_access_token, new_refresh_token)


from celery import shared_task 
from Aleucos.crm import crm
from loguru import logger


@shared_task
def refresh_tokens_task() -> None:
    crm.refresh_tokens()


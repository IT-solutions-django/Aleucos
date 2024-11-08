from celery import shared_task
from django.core.files.uploadedfile import UploadedFile
from .services import OrderImporter, ImportOrderStatusService
from loguru import logger


@shared_task
def import_orders_from_xlsx_task(xlsx_file_path: str, manager_email: str) -> None:
    log_text = 'Началась загрузка заказа из файла'
    logger.info(log_text)
    ImportOrderStatusService.process(log_text, manager_email)

    with open(xlsx_file_path, 'rb') as f:
        xlsx_file = UploadedFile(f)
        OrderImporter.import_order_from_xlsx(xlsx_file, manager_email) 


@shared_task
def delete_import_statuses_task() -> None: 
    ImportOrderStatusService.delete_all()
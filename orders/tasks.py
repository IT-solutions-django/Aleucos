from celery import shared_task
from django.core.files.uploadedfile import UploadedFile
from .services import OrderImporter, ImportOrderStatusService
from loguru import logger


@shared_task
def import_orders_from_xlsx_task(xlsx_file_path: str) -> None:

    with open(xlsx_file_path, 'rb') as f:
        xlsx_file = UploadedFile(f)

        OrderImporter.import_order_from_xlsx(xlsx_file) 

    delete_import_statuses_task.apply_async(countdown=60*15)


@shared_task
def delete_import_statuses_task() -> None: 
    ImportOrderStatusService.delete_statuses_of_order()
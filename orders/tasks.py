from celery import shared_task
from django.core.files.uploadedfile import UploadedFile
from .services import OrderImporter, ImportOrderStatusService
from loguru import logger


@shared_task
def import_orders_from_xlsx_task(xlsx_file_path: str) -> None:
    log_text = 'Началась загрузка заказа из файла'
    logger.info(log_text)
    ImportOrderStatusService.add_new_status(log_text)


    with open(xlsx_file_path, 'rb') as f:
        xlsx_file = UploadedFile(f)

        OrderImporter.import_order_from_xlsx(xlsx_file) 

        log_text = 'Началась загрузка новых данных из файла'
        logger.info(log_text)
        ImportOrderStatusService.add_new_status(log_text)

    log_text = 'Загрузка данных завершена'
    logger.info(log_text)
    ImportOrderStatusService.add_new_status(log_text)

    delete_import_statuses_task.apply_async(countdown=60*15)


@shared_task
def delete_import_statuses_task() -> None: 
    ImportOrderStatusService.delete_statuses_of_order()
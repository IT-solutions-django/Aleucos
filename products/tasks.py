from celery import shared_task 
from django.core.files.uploadedfile import UploadedFile
from loguru import logger
from .services import ProductImporter, ElasticSearchService, ImportStatusService


@shared_task
def import_products_from_xlsx_task(xlsx_file_path: str, user_id: int) -> None:
    ImportStatusService.delete_all_statuses()
    ElasticSearchService.truncate_products_index()

    log_text = 'Началось удаление неактуальных данных'
    logger.info(log_text)
    ImportStatusService.add_new_status(log_text)

    with open(xlsx_file_path, 'rb') as f:
        xlsx_file = UploadedFile(f)

        ProductImporter.truncate_products_and_brands() 

        log_text = 'Началась загрузка новых данных из файла'
        logger.info(log_text)
        ImportStatusService.add_new_status(log_text)

        imported_products_count = ProductImporter.import_products_from_xlsx(xlsx_file, user_id) 

    log_text = 'Загрузка данных завершена'
    logger.info(log_text)
    ImportStatusService.add_new_status(log_text)

    ElasticSearchService.add_all_products_to_index()

    log_text = f'Обработано {imported_products_count} товаров'
    logger.info(log_text)
    ImportStatusService.add_new_status(log_text)

    delete_import_statuses_task.apply_async(countdown=60*30)
    return imported_products_count


@shared_task
def delete_import_statuses_task() -> None: 
    ImportStatusService.delete_all_statuses()



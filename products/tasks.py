from celery import shared_task 
from django.core.files.uploadedfile import UploadedFile
from loguru import logger
from .services import ProductImporter, ElasticSearchService, ImportStatusService


@shared_task
def import_products_from_xlsx_task(xlsx_file_path: str, user_id: int) -> None:

    ElasticSearchService.truncate_products_index()
    logger.info('Началось удаление неактуальных данных')
    ImportStatusService.delete_all_statuses()
    ImportStatusService.add_new_status('Началось удаление неактуальных данных')

    with open(xlsx_file_path, 'rb') as f:
        xlsx_file = UploadedFile(f)

        ProductImporter.truncate_products_and_brands() 
        logger.info('Началась загрузка новых данных из файла')
        ImportStatusService.add_new_status('Началась загрузка новых данных из файла')

        imported_products_count = ProductImporter.import_products_from_xlsx(xlsx_file, user_id) 

    logger.info('Загрузка данных завершена')
    ImportStatusService.add_new_status('Загрузка данных завершена')

    ElasticSearchService.add_all_products_to_index()

    logger.info(f'Обработано {imported_products_count} товаров')
    ImportStatusService.add_new_status(f'Обработано {imported_products_count} товаров')

    delete_import_statuses_task.apply_async(countdown=60*30)

    return imported_products_count


@shared_task
def delete_import_statuses_task() -> None: 
    ImportStatusService.delete_all_statuses()
from celery import shared_task 
from django.core.files.uploadedfile import UploadedFile
from loguru import logger
from .services import CatalogImporter, ElasticSearchService, ImportProductsStatusService, CatalogExporter
from Aleucos import settings


@shared_task
def import_products_from_xlsx_task(xlsx_file_path: str) -> None:
    settings.ELASTICSEARCH_SYNC = False
    ImportProductsStatusService.delete_all_statuses()
    ElasticSearchService.truncate_products_index()

    log_text = 'Началось удаление неактуальных данных'
    logger.info(log_text)
    ImportProductsStatusService.add_new_status(log_text)

    with open(xlsx_file_path, 'rb') as f:
        xlsx_file = UploadedFile(f)

        CatalogImporter.truncate_not_frozen_products_and_brands() 

        log_text = 'Началась загрузка новых данных из файла'
        logger.info(log_text)
        ImportProductsStatusService.add_new_status(log_text)

        imported_products_count = CatalogImporter.import_catalog_from_xlsx(xlsx_file) 

    log_text = 'Загрузка данных завершена'
    logger.info(log_text)
    ImportProductsStatusService.add_new_status(log_text)

    ElasticSearchService.add_all_products_to_index()

    log_text = f'Обработано {imported_products_count} товаров'
    logger.info(log_text)
    ImportProductsStatusService.add_new_status(log_text)

    settings.ELASTICSEARCH_SYNC = True
    delete_import_statuses_task.apply_async(countdown=60*1)
    return imported_products_count


@shared_task
def delete_import_statuses_task() -> None: 
    ImportProductsStatusService.delete_all_statuses()


@shared_task
def export_catalog_task() -> None: 
    CatalogExporter.export_catalog_to_xlsx()
from celery import shared_task 
from django.core.files.uploadedfile import UploadedFile
from loguru import logger
from .services import CatalogImporter, ElasticSearchService, ImportProductsStatusService, CatalogExporter
from Aleucos import settings


@shared_task
def import_products_from_xlsx_task(xlsx_file_path: str) -> None:
    settings.ELASTICSEARCH_SYNC = False

    log_text = 'Началась загрузка новых данных из файла'
    logger.info(log_text)
    ImportProductsStatusService.process(log_text)

    with open(xlsx_file_path, 'rb') as f:
        xlsx_file = UploadedFile(f)

        CatalogImporter.import_catalog_from_xlsx(xlsx_file) 

    ElasticSearchService.add_all_products_to_index()

    settings.ELASTICSEARCH_SYNC = True


@shared_task
def delete_import_statuses_task() -> None: 
    ImportProductsStatusService.delete_all()


@shared_task
def export_catalog_task() -> None: 
    CatalogExporter.export_catalog_to_xlsx()
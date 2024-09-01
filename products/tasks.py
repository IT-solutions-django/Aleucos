from celery import shared_task 
from django.core.files.uploadedfile import UploadedFile
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from .services import import_products_from_xlsx, truncate_products_and_brands, ElasticSearchService
from .models import Product


@shared_task
def import_products_from_xlsx_task(xlsx_file_path: str, user_id: int) -> None:

    ElasticSearchService.truncate_products_index()

    with open(xlsx_file_path, 'rb') as f:
        xlsx_file = UploadedFile(f)

        truncate_products_and_brands()  
        imported_products_count = import_products_from_xlsx(xlsx_file, user_id) 

    ElasticSearchService.add_all_products_to_index()
    

    LogEntry.objects.log_action(
        user_id=user_id,
        content_type_id=ContentType.objects.get_for_model(Product).pk,
        object_id=None,
        object_repr=f'Импортировано {imported_products_count} товаров' ,
        action_flag=ADDITION
    )

    return imported_products_count



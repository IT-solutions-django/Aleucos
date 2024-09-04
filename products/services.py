from django.core.files.base import ContentFile 
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from openpyxl_image_loader import SheetImageLoader
from decimal import Decimal, getcontext, ROUND_HALF_UP
from openpyxl.reader.excel import load_workbook
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models 
from django.db.models.query import QuerySet
import io
import os 
from loguru import logger

from .models import Product, Brand, ImportStatus
from .exceptions import ProductImportError, EndOfTable
from .documents import ProductDocument
from Aleucos import settings


class ProductImporter:
    @staticmethod
    def import_products_from_xlsx(xlsx_file: UploadedFile, user_id: int) -> int:
        workbook = load_workbook(filename=xlsx_file, data_only=True)
        worksheet = workbook.worksheets[1]
        image_loader = SheetImageLoader(worksheet)

        updated_products_count = 0

        for index, row in enumerate(worksheet.iter_rows(min_row=4, max_row=500, values_only=True), 4):
            try:
                ProductImporter.process_product_row(index, row, image_loader)

                updated_products_count += 1
                if updated_products_count % 100 == 0: 
                    ImportStatusService.add_new_status(f'Обработано {updated_products_count} товаров')

            except EndOfTable:
                break
            except ProductImportError as e:
                logger.error(str(e))

        return updated_products_count

    @staticmethod
    def process_product_row(index: int, row: tuple, image_loader: SheetImageLoader) -> None:
        barcode = str(row[0])
        brand_title = str(row[1])
        title = str(row[2])
        description = str(row[3])
        photo = row[4]
        volume = str(row[5])
        weight = row[6]
        notes = str(row[7])
        price_before_200k = row[9]
        price_after_200k = row[10]
        price_after_500k = row[11]
        is_in_stock = True if str(row[12]) == '0' else False

        if not brand_title and not title and not barcode:
            raise EndOfTable()

        ProductImporter.validate_product_data(barcode, title, price_before_200k, price_after_200k, price_after_500k)

        photo = ProductImporter.get_image_or_none(barcode, index, image_loader)
        if photo is None:
            photo = settings.DEFAULT_IMAGE_PATH
        else:
            ProductImporter.delete_image_if_exists(photo.name)

        if weight is not None:
            weight = ProductImporter.convert_str_to_decimal(str(weight))
        price_before_200k = ProductImporter.convert_str_to_decimal(str(price_before_200k))
        price_after_200k = ProductImporter.convert_str_to_decimal(str(price_after_200k))
        price_after_500k = ProductImporter.convert_str_to_decimal(str(price_after_500k))

        brand, _ = Brand.objects.get_or_create(title=brand_title)

        try:
            Product.objects.update_or_create(
                barcode=barcode,
                defaults={
                    'brand': brand,
                    'title': title,
                    'description': description,
                    'photo': photo,
                    'volume': volume,
                    'weight': weight,
                    'notes': notes,
                    'price_before_200k': price_before_200k,
                    'price_after_200k': price_after_200k,
                    'price_after_500k': price_after_500k,
                    'is_in_stock': is_in_stock
                }
            )

            logger.info(f'Товар "{title}" сохранён в базу данных')
        except (IntegrityError, ValidationError, TypeError) as e:
            raise ProductImportError(f'Ошибка в строке {index}: {str(e)}')

    @staticmethod
    def get_image_or_none(barcode: str, row_index: int, image_loader: SheetImageLoader) -> ContentFile | None:
        try:
            image = image_loader.get(f'E{row_index}')
            image_stream = io.BytesIO()
            image.save(image_stream, format='PNG')
            image_stream.seek(0)
            return ContentFile(image_stream.read(), f'{barcode}.png')
        except Exception:
            return None

    @staticmethod
    def delete_image_if_exists(image_name: str) -> bool:
        image_path = os.path.join('products', image_name)
        if default_storage.exists(image_path):
            default_storage.delete(image_path)

    @staticmethod
    def convert_str_to_decimal(value: str) -> Decimal:
        getcontext().clamp = 1
        value = Decimal(float(str(value).replace(',', '.')))
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def validate_product_data(barcode: str | None,
                              title: str | None,
                              price_before_200k: float | None,
                              price_after_200k: float | None,
                              price_after_500k: float | None) -> None:
        if not title:
            raise ProductImportError(f'У товара со штрихкодом {barcode} отсутствует название')
        elif not barcode or str(barcode) == '0':
            raise ProductImportError(f'У товара {title} отсутствует штрихкод')
        elif any(price in (None, 0) for price in (price_before_200k, price_after_200k, price_after_500k)):
            raise ProductImportError(f'У товара {title} со штрихкодом {barcode} отсутствует цена')
        elif not str(barcode).strip().isnumeric():
            raise ProductImportError(f'У товара неверный штрихкод: {barcode}')

    @staticmethod
    def truncate_products_and_brands() -> None:
        Product.objects.all().delete()
        Brand.objects.all().delete()


class ElasticSearchService: 
    @staticmethod
    def truncate_products_index() -> None: 
        ProductDocument().search().query('match_all').delete() 

    @staticmethod 
    def add_all_products_to_index() -> None: 
        ProductDocument().update(Product.objects.all())


class ImportStatusService: 
    @staticmethod 
    def add_new_status(text: str) -> None: 
        ImportStatus.objects.create(text=text).save()

    def get_all_statuses() -> QuerySet[ImportStatus]: 
        return ImportStatus.objects.all().order_by('time')
    
    def delete_all_statuses() -> None: 
        ImportStatus.objects.all().delete()


def get_max_product_price() -> Decimal: 
    max_price = Product.objects.aggregate(models.Max('price_before_200k'))['price_before_200k__max']
    return max_price

 
def get_paginated_collection(request, collection: QuerySet, count_per_page: int = 10): 
    paginator = Paginator(collection, count_per_page)
    page_number = request.GET.get('page', 1)
    try:
        collection = paginator.page(page_number)
    except PageNotAnInteger:
        collection = paginator.page(1)
    except EmptyPage:
        collection = paginator.page(paginator.num_pages) 
    return collection


def get_all_model_objects(model: models.Model) -> QuerySet: 
    return model.objects.all()
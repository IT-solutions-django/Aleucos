import random
from django.core.files.base import ContentFile 
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from openpyxl_image_loader import SheetImageLoader
from openpyxl.drawing.image import Image
from decimal import Decimal, getcontext, ROUND_HALF_UP
from openpyxl.reader.excel import load_workbook
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models 
from django.db.models.query import QuerySet
from django.db.models import Q
import io
import os 
from loguru import logger
from .models import Category, Product, Brand, ImportProductsStatus
from .exceptions import ProductImportError, EndOfTable
from .documents import ProductDocument
from Aleucos import settings


class CatalogImporter:
    @staticmethod
    def import_catalog_from_xlsx(xlsx_file: UploadedFile) -> int:
        workbook = load_workbook(filename=xlsx_file, data_only=True)
        worksheet = workbook.worksheets[1]
        image_loader = SheetImageLoader(worksheet)

        updated_products_count = 0

        for index, row in enumerate(worksheet.iter_rows(min_row=4, values_only=True), 4):
            try:
                CatalogImporter.process_row(index, row, image_loader)

                updated_products_count += 1
                if updated_products_count % 100 == 0: 
                    ImportProductsStatusService.add_new_status(f'Обработано {updated_products_count} товаров')

            except EndOfTable:
                break
            except ProductImportError as e:
                logger.error(str(e))

        return updated_products_count

    @staticmethod
    def process_row(index: int, row: tuple, image_loader: SheetImageLoader) -> None:
        barcode = row[0]
        brand_title = row[1]
        title = row[2]
        description = str(row[3])
        photo = row[4]
        volume = row[5]
        weight = row[6]
        notes = row[7]
        price_before_200k = row[9]
        price_after_200k = row[10]
        price_after_500k = row[11]
        is_in_stock = True if str(row[12]) == '0' else False

        if brand_title is None and title is None and barcode is None:
            raise EndOfTable()

        CatalogImporter.validate_product_data(barcode, title, price_before_200k, price_after_200k, price_after_500k)

        if Product.objects.filter(barcode=barcode).exists():
            logger.warning(f'Продукт с штрихкодом "{barcode}" уже существует. Пропуск продукта {title}')
            return
        
        photo = CatalogImporter.get_image_or_none(barcode, index, image_loader)
        if photo is None:
            photo = settings.DEFAULT_IMAGE_PATH
        else:
            CatalogImporter.delete_image_if_exists(photo.name)

        if weight is not None:
            weight = CatalogImporter.convert_str_to_decimal(str(weight))
        price_before_200k = CatalogImporter.convert_str_to_decimal(str(price_before_200k))
        price_after_200k = CatalogImporter.convert_str_to_decimal(str(price_after_200k))
        price_after_500k = CatalogImporter.convert_str_to_decimal(str(price_after_500k))

        brand, _ = Brand.objects.get_or_create(title=str(brand_title))

        try:
            product = Product.objects.filter(barcode=barcode).first()

            if product: 
                if product.is_frozen: 
                    product.brand=brand 
                    product.title=title
                    product.description=description
                    product.photo = photo
                    product.volume=volume 
                    product.weight=weight,
                    product.notes=notes,
                    product.price_before_200k=price_before_200k,
                    product.price_after_200k=price_after_200k,
                    product.price_after_500k=price_after_500k,
                    product.is_in_stock=is_in_stock,
                    product.category=random.choice(Category.objects.all()),
                    product.remains=random.randint(0, 100) if is_in_stock else 0
                    
                    product.save(while_importing_catalog=True)
                    return
                else: 
                    raise ProductImportError(f'Товар со штрихкодом {barcode} уже есть в базе данных')

            product = Product(
                barcode=barcode,
                brand=brand,
                title=title,
                description=description,
                photo=photo,
                volume=volume,
                weight=weight,
                notes=notes,
                price_before_200k=price_before_200k,
                price_after_200k=price_after_200k,
                price_after_500k=price_after_500k,
                is_in_stock=is_in_stock,
                category=random.choice(Category.objects.all()),
                remains=random.randint(0, 100) if is_in_stock else 0
            )
            product.save(while_importing_catalog=True)

            logger.info(f'Товар "{title}" сохранён в базу данных')
        except (ValidationError, TypeError) as e:
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
        return value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

    @staticmethod
    def validate_product_data(barcode: str | float | None,
                              title: str | None,
                              price_before_200k: float | None,
                              price_after_200k: float | None,
                              price_after_500k: float | None) -> None:
        if title is None:
            raise ProductImportError(f'У товара со штрихкодом {barcode} отсутствует название')
        elif barcode is None or str(barcode) == '0':
            raise ProductImportError(f'У товара {title} отсутствует штрихкод')
        elif any(price in (None, 0) for price in (price_before_200k, price_after_200k, price_after_500k)):
            raise ProductImportError(f'У товара {title} со штрихкодом {barcode} отсутствует цена')
        elif not str(barcode).strip().isnumeric():
            raise ProductImportError(f'У товара неверный штрихкод: {barcode}')

    @staticmethod
    def truncate_not_frozen_products_and_brands() -> None:
        Product.objects.filter(is_frozen=False).delete()
        Brand.objects.filter(~Q(products__is_frozen=True)).delete()


class CatalogExporter: 
    @staticmethod
    def export_catalog_to_xlsx() -> str:
        logger.info('Начался экспорт каталога')

        catalog_template_path = os.path.join(settings.MEDIA_ROOT, 'catalog', settings.EXPORT_CATALOG_TEMPLATE_FILENAME)
        exported_catalog_path = os.path.join(settings.MEDIA_ROOT, 'catalog', settings.EXPORT_CATALOG_FILENAME)

        try:
            workbook = load_workbook(filename=catalog_template_path, data_only=True)
        except PermissionError: 
            logger.error('Ошибка при экспорте каталога: файл занят другим процессом')
        worksheet = workbook.worksheets[1]

        products = Product.objects.all()

        current_row_index = 4
        for product in products: 
            image_path = os.path.join(settings.MEDIA_ROOT, product.photo.name)
            image = Image(image_path)
            image.width, image.height = 100, 100
            

            worksheet[f'A{current_row_index}'] = str(product.barcode)
            worksheet[f'B{current_row_index}'] = product.brand.title
            worksheet[f'C{current_row_index}'] = product.title
            worksheet[f'D{current_row_index}'] = product.description
            worksheet.add_image(image, f'E{current_row_index}')
            worksheet[f'F{current_row_index}'] = product.volume
            worksheet[f'G{current_row_index}'] = product.weight
            worksheet[f'H{current_row_index}'] = product.notes
            worksheet[f'J{current_row_index}'] = product.price_before_200k
            worksheet[f'K{current_row_index}'] = product.price_after_200k
            worksheet[f'L{current_row_index}'] = product.price_after_500k
            worksheet[f'M{current_row_index}'] = 0 if product.is_in_stock else None

            current_row_index += 1

        workbook.save(exported_catalog_path)
        logger.info('Каталог был экспортирован')

        return exported_catalog_path


class ElasticSearchService: 
    @staticmethod
    def truncate_products_index() -> None:
        ProductDocument().search().query('match_all').delete() 

    @staticmethod 
    def add_all_products_to_index() -> None: 
        ProductDocument().update(Product.objects.all())


class ImportProductsStatusService: 
    @staticmethod 
    def add_new_status(text: str) -> None: 
        ImportProductsStatus.objects.create(text=text).save()

    def get_all_statuses() -> QuerySet[ImportProductsStatus]: 
        return ImportProductsStatus.objects.all().order_by('time')
    
    def delete_all_statuses() -> None: 
        ImportProductsStatus.objects.all().delete()


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

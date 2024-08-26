from django.core.files.base import ContentFile 
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from openpyxl_image_loader import SheetImageLoader
from decimal import Decimal, getcontext, ROUND_HALF_UP
from openpyxl.reader.excel import load_workbook
import io
from django.core.files.uploadedfile import UploadedFile

from .models import Product, Brand
from .exceptions import ProductImportError, EndOfTable


def import_products_from_xlsx(xlsx_file: UploadedFile) -> tuple[int, list[str]]:
    workbook = load_workbook(filename=xlsx_file, data_only=True)
    worksheet = workbook.worksheets[1]
    image_loader = SheetImageLoader(worksheet)

    updated_products_count = 0
    errors = []

    for index, row in enumerate(worksheet.iter_rows(min_row=4, values_only=True), 4):
        try:
            process_product_row(index, row, image_loader)
            updated_products_count += 1
        except EndOfTable: 
            break
        except ProductImportError as e:
            errors.append(str(e))

    return updated_products_count, errors


def process_product_row(index: int, row: tuple, image_loader: SheetImageLoader) -> None:
    barcode = row[0]
    brand_title = row[1]
    title = row[2]
    description = row[3]
    photo = row[4]
    volume = row[5]
    weight = row[6]
    notes = row[7]
    price_before_200k = row[9]
    price_after_200k = row[10]
    price_after_500k = row[11]
    is_in_stock = True if str(row[12]) == '0' else False

    if not brand_title and not title and not barcode:
        raise EndOfTable()
    
    validate_product_data(barcode, title, price_before_200k, price_after_200k, price_after_500k)

    photo = get_image(barcode, index, image_loader)
    if weight is not None:
        weight = convert_float_to_decimal(weight)
    price_before_200k = convert_float_to_decimal(price_before_200k)
    price_after_200k = convert_float_to_decimal(price_after_200k)
    price_after_500k = convert_float_to_decimal(price_after_500k)

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
    except (IntegrityError, ValidationError, TypeError) as e:
        raise ProductImportError(f'Ошибка в строке {index}: {str(e)}')
    

def get_image(barcode: str, row_index: int, image_loader: SheetImageLoader) -> ContentFile | None:
    try:
        image = image_loader.get(f'E{row_index}')
        image_stream = io.BytesIO()
        image.save(image_stream, format='PNG')
        image_stream.seek(0)
        return ContentFile(image_stream.read(), f'{barcode}.png')
    except (KeyError, ValueError):
        return None
    

def convert_float_to_decimal(value: float) -> Decimal:
    getcontext().clamp = 1
    value = Decimal(str(value).replace(',', '.'))
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def validate_product_data(barcode: str, title: str, price_before_200k: float, price_after_200k: float, price_after_500k: float):
    if not title:
        raise ProductImportError(f'У товара со штрихкодом {barcode} отсутствует название')
    elif any(price in (None, 0) for price in (price_before_200k, price_after_200k, price_after_500k)):
        raise ProductImportError(f'У товара {title} со штрихкодом {barcode} отсутствует цена')
    elif not barcode or str(barcode) == '0':
        raise ProductImportError(f'У товара {title} отсутствует штрихкод')
    elif not str(barcode).strip().isnumeric():
        raise ProductImportError(f'У товара неверный штрихкод: {barcode}')
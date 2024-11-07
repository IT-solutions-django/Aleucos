from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from decimal import Decimal, getcontext, ROUND_HALF_UP
from openpyxl.reader.excel import load_workbook
from loguru import logger
from django.db.models.query import QuerySet
from .exceptions import OrderImportError, EndOfTable, CustomerDataError
from .models import OrderStatus, Order, OrderItem, ImportOrderStatus
from products.models import Product
from Aleucos import settings
from users.models import User
from configs.models import Config


class OrderImporter:
    @staticmethod
    def import_order_from_xlsx(xlsx_file: UploadedFile) -> None:
        workbook = load_workbook(filename=xlsx_file, data_only=True)
        customer_data_worksheet = workbook.worksheets[0]
        items_worksheet = workbook.worksheets[1]

        customer_email = customer_data_worksheet.cell(row=19, column=3).value
        print(customer_email)
        if not customer_email: 
            log_text = 'Ошибка! Заказ не был создан: Email покупателя не указан'
            ImportOrderStatusService.add_new_status(log_text)
            logger.error(log_text)
            return

        try:
            user = User.objects.get(email=customer_email)
        except User.DoesNotExist: 
            log_text = f'Ошибка! Заказ не был создан: пользователя с email {customer_email} не существует'
            ImportOrderStatusService.add_new_status(log_text)
            logger.error(log_text)
            return 

        order_data = {
            'user': user,
            'status': OrderStatus.objects.get(title=Config.get_instance().order_status_first),
            'manager': user.manager,
            'items': [],
            'total_price': 0
        }

        for index, row in enumerate(items_worksheet.iter_rows(min_row=4, values_only=True), 4):
            try:
                order_item_data = OrderImporter.process_order_row(index, row)
                if order_item_data:
                    order_data['items'].append(order_item_data)
            except EndOfTable:
                break
            except OrderImportError as e:
                log_text = f'Ошибка! Заказ не был создан: {str(e)}'
                logger.error(log_text)
                ImportOrderStatusService.add_new_status(log_text)
                return 

        OrderImporter.calculate_total_price(order_data)

        order = Order.objects.create(
            user=order_data['user'],
            status=order_data['status'],
            manager=order_data['manager'],
            total_price=order_data['total_price']
        )
        for item_data in order_data['items']:
            OrderItem.objects.create(
                order=order,
                product_name=item_data['product_name'], 
                brand_name=item_data['brand_name'], 
                quantity=item_data['quantity'], 
                unit_price=item_data['unit_price'], 
                total_price=item_data['total_price']
            )
            product = Product.objects.get(barcode=item_data['barcode'])
            product.remains -= item_data['quantity']
            product.save()
            
            log_text = f'В заказ добавлен товар {item_data["product_name"]} ({item_data["quantity"]} шт)'
            logger.info(log_text)
            ImportOrderStatusService.add_new_status(log_text, order)
        order.save()
        order.create_pdf_bill()

        log_text = f'Заказ №{order.number} для клиента {order.user.email} был успешно создан!'
        logger.info(log_text)
        ImportOrderStatusService.add_new_status(log_text, order)

    @staticmethod
    def process_order_row(index: int, row: tuple) -> OrderItem | None:
        barcode = row[0]
        brand_title = row[1]
        title = row[2]
        quantity = int(row[12]) if row[12] is not None else 0 

        if quantity == 0: 
            return 
        if brand_title is None and title is None and barcode is None:
            raise EndOfTable()
        OrderImporter.validate_product_data(barcode, title)

        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist: 
            raise OrderImportError(f'Товара со штрихкодом {barcode} не существует')
        except Product.MultipleObjectsReturned: 
            raise OrderImportError(f'В базе данных существует несколько товаров со штрихкодом {barcode}')
        
        if product.remains - quantity < 0: 
            raise OrderImportError(f'Товара со штрихкодом {barcode} недостаточно на складе ({product.remains} шт. есть, запрашивается {quantity} шт.)')

        price_before_200k = product.price_before_200k

        unit_price = price_before_200k  
        total_price = quantity * unit_price

        return {
            'barcode': product.barcode,
            'product_name': product.title,
            'brand_name': product.brand.title,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price
        }
    
    @staticmethod
    def calculate_total_price(order_data: dict) -> None:
        total_price = sum(item['total_price'] for item in order_data['items'])

        if total_price >= 200000:
            for item in order_data['items']:
                item['unit_price'] = Product.objects.get(barcode=item['barcode']).price_after_200k
                item['total_price'] = item['quantity'] * item['unit_price']
            total_price = sum(item['total_price'] for item in order_data['items'])

        if total_price >= 500000:
            for item in order_data['items']:
                item['unit_price'] = Product.objects.get(barcode=item['barcode']).price_after_500k
                item['total_price'] = item['quantity'] * item['unit_price']
            total_price = sum(item['total_price'] for item in order_data['items'])

        order_data['total_price'] = total_price

    @staticmethod
    def convert_str_to_decimal(value: str) -> Decimal:
        getcontext().clamp = 1
        value = Decimal(float(str(value).replace(',', '.')))
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def validate_product_data(barcode: str | float | None, title: str | None) -> None:
        if title is None:
            raise OrderImportError(f'У товара со штрихкодом {barcode} отсутствует название')
        elif barcode is None or str(barcode) == '0':
            raise OrderImportError(f'У товара {title} отсутствует штрихкод')
       
        elif not str(barcode).strip().isnumeric():
            raise OrderImportError(f'У товара неверный штрихкод: {barcode}')


class ImportOrderStatusService: 
    def add_new_status(text: str, order: Order=None) -> None: 
        if order:
            text = f'Загрузка заказа {order.number}: ' + text
        ImportOrderStatus.objects.create(text=text, order=order) 

    def delete_statuses_of_order() -> None: 
        ImportOrderStatus.objects.all().delete()

    def get_all_statuses_of_order(order: Order=None) -> QuerySet | None: 
        return ImportOrderStatus.objects.all().filter(order=Order)

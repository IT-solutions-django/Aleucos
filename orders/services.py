from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from decimal import Decimal, getcontext, ROUND_HALF_UP
from openpyxl.reader.excel import load_workbook
from loguru import logger
from django.db.models.query import QuerySet
from .exceptions import OrderImportError, EndOfTable
from .models import OrderStatus, Order, OrderItem, ImportOrderStatus
from products.models import Product
from Aleucos import settings
from users.models import User
from configs.models import Config
from orders.models import PaymentMethod, DeliveryTerm


class OrderImporter:
    @staticmethod
    def import_order_from_xlsx(
        xlsx_file: UploadedFile, 
        manager_email: str,
        payment_method_id: int, 
        delivery_terms_id: int, 
        comment: str, 
        user_id: int
    ) -> None:
        workbook = load_workbook(filename=xlsx_file, data_only=True)
        items_worksheet = workbook.worksheets[1]

        user = User.objects.get(pk=user_id)
        
        try: 
            manager = User.objects.get(email=manager_email)
        except User.DoesNotExist: 
            log_text = f'Ошибка! Заказ не был создан: менеджера с email {customer_email} не существует'
            ImportOrderStatusService.error(log_text, manager_email)
            logger.error(log_text)
            return 

        order_data = {
            'user': user,
            'status': OrderStatus.objects.get(title=Config.get_instance().order_status_first),
            'manager': manager,
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
                ImportOrderStatusService.error(log_text, manager_email)
                return 
            
        if len(order_data['items']) == 0: 
            log_text = f'Ошибка! Заказ не был создан: в заказе нет ни одной позиции'
            ImportOrderStatusService.error(log_text, manager_email)
            logger.error(log_text)
            return 

        OrderImporter.calculate_total_price(order_data)

        order = Order.objects.create(
            user=order_data['user'],
            status=order_data['status'],
            manager=order_data['manager'],
            total_price=order_data['total_price'], 
            payment_method=PaymentMethod.objects.get(pk=payment_method_id), 
            delivery_terms=DeliveryTerm.objects.get(pk=delivery_terms_id), 
            comment=comment
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
            ImportOrderStatusService.process(log_text, manager_email)
        order.save()
        order.create_pdf_bill()

        log_text = f'Заказ №{order.number} для клиента {order.user.email} был успешно создан!' if order.user else f'Заказ №{order.number} был успешно создан!'
        logger.info(log_text)
        ImportOrderStatusService.success(log_text, manager_email)

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
    @staticmethod 
    def info(text: str, manager_email: str) -> None: 
        ImportOrderStatus.objects.create(
            text=text, 
            status_type=ImportOrderStatus.Type.INFO, 
            manager=User.objects.get(email=manager_email)
        ).save()

    @staticmethod 
    def process(text: str, manager_email: str) -> None: 
        ImportOrderStatus.objects.create(
            text=text, 
            status_type=ImportOrderStatus.Type.PROCESS,
            manager=User.objects.get(email=manager_email)
        ).save()

    @staticmethod 
    def error(text: str, manager_email: str) -> None: 
        ImportOrderStatus.objects.create(
            text=text, 
            status_type=ImportOrderStatus.Type.ERROR, 
            manager=User.objects.get(email=manager_email)
        ).save()

    @staticmethod 
    def success(text: str, manager_email: str) -> None: 
        ImportOrderStatus.objects.create(
            text=text, 
            status_type=ImportOrderStatus.Type.SUCCESS, 
            manager=User.objects.get(email=manager_email)
        ).save()

    @staticmethod 
    def delete_all() -> None: 
        ImportOrderStatus.objects.all().delete()

    @staticmethod 
    def get_all_statuses(manager: User) -> QuerySet | None: 
        return ImportOrderStatus.objects.all().filter(manager=manager)

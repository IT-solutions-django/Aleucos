import logging
import json
import requests
import time
from pythonjsonlogger import jsonlogger


class ElasticLogHandler(logging.Handler):
    def __init__(self, host, index):
        super().__init__()
        self.host = host.rstrip('/')
        self.index = index

    def emit(self, record):
        try:
            log_entry = self.format(record)
            url = f'{self.host}/{self.index}/_doc/'
            headers = {'Content-Type': 'application/json'}
            requests.post(url, data=log_entry, headers=headers, timeout=1)
        except Exception as e:
            print(f"Ошибка отправки лога в Elasticsearch: {e}")


class UTCJsonFormatter(jsonlogger.JsonFormatter):
    def converter(self, timestamp):
        return time.gmtime(timestamp) 



business_logger = logging.getLogger("business") 

def log_product_arrival(product, quantity: int, manager_name: str) -> None:
    """Логирует поступление товара в Elasticsearch"""
    missing_info = get_missing_fields(product)

    category_titles = list(product.categories.values_list('title', flat=True))

    business_logger.info(
        "Поступление товара",
        extra={
            "event_type": "product_arrival",
            "categories": category_titles,
            "data": {
                'article': product.article,
                "title": product.title,
                "brand": product.brand,
                "barcode": product.barcode,
                "price_before_200k": product.price_before_200k,
                "categories": category_titles,
                "quantity": quantity, 
                'manager_name': manager_name,
                **missing_info,
            }
        }
    )


def log_product_sale(product, quantity: int, manager_name: str) -> None:
    """Логирует продажу товара в Elasticsearch"""
    category_titles = list(product.categories.values_list('title', flat=True))
    
    business_logger.info(
        "Продажа товара",
        extra={
            "event_type": "product_sale",
            "categories": category_titles,
            "data": {
                'article': product.article,
                "title": product.title,
                "brand": product.brand,
                "barcode": product.barcode,
                "price_before_200k": product.price_before_200k,
                "categories": category_titles,
                "quantity": quantity, 
                'manager_name': manager_name,
            }
        }
    )
    print('лог')


def get_missing_fields(product) -> dict:
    """Определяет отсутствующие поля у товара"""
    required_fields = [
        'barcode',
        'brand', 
        'title_russian', 
        'categories', 
        'photo', 
        'volume',
        'weight', 
        'notes',
        'will_arrive_at',
    ]
    missing_info = {}

    for field in required_fields:
        value = getattr(product, field, None)
        missing_info[f"missing_{field}"] = value is None or value == ''

    return missing_info
import json
from collections import UserDict
from decimal import ROUND_HALF_UP, Decimal, getcontext
from products.models import Product
from enum import Enum

class Cart(UserDict):
    changed = False 

    class KeyNames:
        PRODUCTS = 'products' 
        QUANTITY = 'quantity'
        UNIT_PRICE_BEFORE_200K = 'unit_price_before_200k'
        UNIT_PRICE_AFTER_200K = 'unit_price_after_200k'
        UNIT_PRICE_AFTER_500K = 'unit_price_after_500k'
        UNIT_PRICE = 'unit_price'
        TOTAL_PRODUCT_PRICE = 'total_product_price'
        TOTAL_CART_PRICE = 'total_price'

    def change(self, product: Product, quantity=0, append=False) -> dict:
        self.changed = True
        barcode = str(product.barcode)

        k = self.KeyNames

        self.setdefault(k.PRODUCTS, {})
        self.setdefault(k.TOTAL_CART_PRICE, 0)
        self[k.PRODUCTS].setdefault(barcode, {
            k.QUANTITY: 0,
            k.UNIT_PRICE_BEFORE_200K: product.price_before_200k,
            k.UNIT_PRICE_AFTER_200K: product.price_after_200k,
            k.UNIT_PRICE_AFTER_500K: product.price_after_500k,
            k.UNIT_PRICE: 0,
            k.TOTAL_PRODUCT_PRICE: 0,
        })

        if append:
            self[k.PRODUCTS][barcode][k.QUANTITY] += quantity
            print(f'append=true\nТекущее количество={self[k.PRODUCTS][barcode][k.QUANTITY]}')
        else:
            self[k.PRODUCTS][barcode][k.QUANTITY] = quantity
            print(f'append=false\nТекущее количество={self[k.PRODUCTS][barcode][k.QUANTITY]}')

        if self[k.PRODUCTS][barcode][k.QUANTITY] <= 0:
            print('Удаляем товар')
            del self[k.PRODUCTS][barcode]
        else:
            unit_price = self[k.PRODUCTS][barcode][k.UNIT_PRICE_BEFORE_200K]
            total_price = unit_price * quantity
            self[k.PRODUCTS][barcode][k.UNIT_PRICE] = unit_price
            self[k.PRODUCTS][barcode][k.TOTAL_PRODUCT_PRICE] = total_price

            self.update_total_order_price()
            if self[k.TOTAL_CART_PRICE] < 200000: 
                for barcode, item in self[k.PRODUCTS].items():
                    new_unit_price = flaot_to_decimal(item[k.UNIT_PRICE_BEFORE_200K])
                    item[k.UNIT_PRICE] = new_unit_price
                    item[k.TOTAL_PRODUCT_PRICE] = new_unit_price * item[k.QUANTITY]

                self.update_total_order_price()
            if self[k.TOTAL_CART_PRICE] >= 200000: 
                for barcode, item in self[k.PRODUCTS].items():
                    new_unit_price = flaot_to_decimal(item[k.UNIT_PRICE_AFTER_200K] )
                    item[k.UNIT_PRICE] = new_unit_price
                    item[k.TOTAL_PRODUCT_PRICE] = new_unit_price * item[k.QUANTITY]
                    
                self.update_total_order_price()
            if self[k.TOTAL_CART_PRICE] >= 500000: 
                for barcode, item in self[k.PRODUCTS].items():
                    new_unit_price = flaot_to_decimal(item[k.UNIT_PRICE_AFTER_500K])
                    item[k.UNIT_PRICE] = new_unit_price
                    item[k.TOTAL_PRODUCT_PRICE] = new_unit_price * item[k.QUANTITY]

        self.update_total_order_price()

        return self
    
    def remove(self, barcode: str) -> None: 
        self.changed = True
        del self[Cart.KeyNames.PRODUCTS][barcode]
        
    def update_total_order_price(self) -> None:
        k = self.KeyNames
        getcontext().clamp = 1
        self[k.TOTAL_CART_PRICE] = sum(
            Decimal(item[k.TOTAL_PRODUCT_PRICE]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) for item in self[k.PRODUCTS].values()
        )

    def flush(self) -> None:
        k = self.KeyNames
        self.changed = True
        self.data = {
            k.PRODUCTS: {},
            k.TOTAL_CART_PRICE: 0
        }
        
    def to_dict(self) -> dict:
        k = self.KeyNames

        if k.PRODUCTS not in self:
            self[k.PRODUCTS] = {}
        if k.TOTAL_CART_PRICE not in self:
            self[k.TOTAL_CART_PRICE] = 0

        def convert_value(value):
            if isinstance(value, Decimal):
                return float(value)  
            return value

        return {
            k.PRODUCTS: {
                barcode: {
                    k.QUANTITY: convert_value(item[k.QUANTITY]),
                    k.UNIT_PRICE_BEFORE_200K: convert_value(item[k.UNIT_PRICE_BEFORE_200K]),
                    k.UNIT_PRICE_AFTER_200K: convert_value(item[k.UNIT_PRICE_AFTER_200K]),
                    k.UNIT_PRICE_AFTER_500K: convert_value(item[k.UNIT_PRICE_AFTER_500K]),
                    k.TOTAL_PRODUCT_PRICE: convert_value(item[k.TOTAL_PRODUCT_PRICE]),
                    k.UNIT_PRICE: convert_value(item[k.UNIT_PRICE])
                }
                for barcode, item in self[k.PRODUCTS].items()
            },
            k.TOTAL_CART_PRICE: convert_value(self[k.TOTAL_CART_PRICE])
        }


def flaot_to_decimal(number: float) -> Decimal: 
    return Decimal(number).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
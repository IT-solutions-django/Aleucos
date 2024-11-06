HEIGHT = 841.89
WIDTH = 595.27

LEFT = 34
RIGHT = WIDTH - 72
BOTTOM = 50
TOP = HEIGHT - 50

FONT_SIZE = 9

class UpperGrid:
    HEIGHT = 95
    QR_CODE_WIDTH = 73.46
    ACCOUNT_WIDTH = 110
    FIRST_CELL_WIDTH = 268
    FIRST_CELL_HEIGHT = 45
    INN_HEIGHT = 14.3
    INN_WIDTH = 148
    BOTTOM_MARGIN = 26

class Header: 
    Y_POSITION = TOP - UpperGrid.HEIGHT - UpperGrid.BOTTOM_MARGIN
    HEIGHT = 55
    FONT_SIZE = 14

class ContractInfoBlock: 
    Y_POSITION = TOP - UpperGrid.HEIGHT - Header.HEIGHT
    HEIGHT = 105

class ItemsTable: 
    Y_POSITION = TOP - UpperGrid.HEIGHT - UpperGrid.BOTTOM_MARGIN - ContractInfoBlock.HEIGHT
    ROW_HEIGHT = 20
    HEADER_HEIGHT = 13

    NUMBER_COLUMN_WIDTH = 25
    NAME_COLUMN_WIDTH = 240
    QUANTITY_COLUMN_WIDTH = 45
    MEASURE_COLUMN_WIDTH = 30
    PRICE_COLUMN_WIDTH = 60
    TOTAL_PRICE_COLUMN_WIDTH = 60

    NUMBER_COLUMN_X_POS = LEFT
    NAME_COLUMN_X_POS = NUMBER_COLUMN_X_POS + NUMBER_COLUMN_WIDTH
    QUANTITY_COLUMN_X_POS = NAME_COLUMN_X_POS + NAME_COLUMN_WIDTH
    MEASURE_COLUMN_X_POS = QUANTITY_COLUMN_X_POS + QUANTITY_COLUMN_WIDTH
    PRICE_COLUMN_X_POS = MEASURE_COLUMN_X_POS + MEASURE_COLUMN_WIDTH
    TOTAL_PRICE_COLUMN_X_POS = PRICE_COLUMN_X_POS + PRICE_COLUMN_WIDTH

    MARGIN_BOTTOM = 15

    def get_height(items_count: int) -> float: 
        return ItemsTable.HEADER_HEIGHT + ItemsTable.ROW_HEIGHT * items_count
    

class BottomText: 
    def get_y_position(items_count: int) -> float: 
        return ItemsTable.Y_POSITION - ItemsTable.get_height(items_count) - 60


MONTHS_MAPPER = {
    1: 'января', 
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря',
}
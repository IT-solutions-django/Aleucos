from collections.abc import Iterable
import reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfgen import textobject
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from django.conf import settings
from .config import *
from .utils import (
    split_text_into_lines, 
    get_current_date_str, 
    get_formatted_price, 
    convert_price_to_words
)


def generate_pdf_bill(
        output_filename: str, 
        pdf_title: str, 
        items: Iterable, 
        order
    ) -> None: 
    print(items)

    pdf = canvas.Canvas(output_filename)
    pdf.setTitle(pdf_title) 

    styles = getSampleStyleSheet()
    reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + '/orders/pdf_generator/fonts')
    styles['Normal'].fontName='Arial'
    styles['Heading1'].fontName='Arial'
    pdfmetrics.registerFont(TTFont('Arial','Arial.ttf', 'UTF-8'))
    pdfmetrics.registerFont(TTFont('BoldArial','Arial3.ttf', 'UTF-8'))
    
    _print_upper_grid(pdf)
    _print_upper_grid_text(pdf)
    _print_header_text(pdf)
    _print_contract_info(pdf, order)
    _print_items_grid(pdf, items)
    _print_items_grid_header_text(pdf)
    _print_items_grid_text(pdf, items)
    _print_total_price_text(pdf, order, items)
    _print_bottom_text(pdf, order, items)

    pdf.save()


def _print_upper_grid(pdf: canvas.Canvas) -> None: 
    pdf.setLineWidth(0.6)
    upper_grid_lines = [
        (LEFT, TOP, RIGHT, TOP),
        (RIGHT, TOP, RIGHT, TOP - UpperGrid.HEIGHT),
        (LEFT, TOP - UpperGrid.HEIGHT, RIGHT, TOP - UpperGrid.HEIGHT),
        (LEFT, TOP, LEFT, TOP - UpperGrid.HEIGHT),

        (RIGHT - UpperGrid.QR_CODE_WIDTH, TOP, RIGHT - UpperGrid.QR_CODE_WIDTH, TOP - UpperGrid.HEIGHT),
        (RIGHT - UpperGrid.QR_CODE_WIDTH - UpperGrid.ACCOUNT_WIDTH, TOP, RIGHT -
         UpperGrid.QR_CODE_WIDTH - UpperGrid.ACCOUNT_WIDTH, TOP - UpperGrid.HEIGHT),
        (LEFT + UpperGrid.FIRST_CELL_WIDTH, TOP, LEFT + UpperGrid.FIRST_CELL_WIDTH, TOP - UpperGrid.HEIGHT),
        (LEFT + UpperGrid.INN_WIDTH, TOP - UpperGrid.FIRST_CELL_HEIGHT, 
         LEFT + UpperGrid.INN_WIDTH, TOP - UpperGrid.FIRST_CELL_HEIGHT - UpperGrid.INN_HEIGHT),

        (LEFT, TOP - UpperGrid.FIRST_CELL_HEIGHT, 
         RIGHT - UpperGrid.QR_CODE_WIDTH, TOP - UpperGrid.FIRST_CELL_HEIGHT),
        (LEFT, TOP - UpperGrid.HEIGHT + 36, 
         LEFT + UpperGrid.FIRST_CELL_WIDTH, TOP - UpperGrid.HEIGHT + 36),
        (LEFT + UpperGrid.FIRST_CELL_WIDTH, TOP - UpperGrid.INN_HEIGHT, 
         RIGHT - UpperGrid.QR_CODE_WIDTH - UpperGrid.ACCOUNT_WIDTH, TOP - UpperGrid.INN_HEIGHT)
    ]

    pdf.lines(upper_grid_lines)


def _print_upper_grid_text(pdf: canvas.Canvas) -> None: 
    textobject = pdf.beginText()
    LEFT_TEXT_POSITION = LEFT + 2

    textobject.setFont('Arial', FONT_SIZE)
    textobject.setTextOrigin(LEFT_TEXT_POSITION, TOP - FONT_SIZE)
    textobject.textLine('Филиал "Центральный" Банка ВТБ (ПАО) г. Москва')

    textobject.setTextOrigin(LEFT_TEXT_POSITION, TOP - FONT_SIZE - UpperGrid.FIRST_CELL_HEIGHT - 1)
    textobject.textLine('ИНН     250999742802')

    textobject.setTextOrigin(LEFT + 2 + UpperGrid.INN_WIDTH, TOP - FONT_SIZE - UpperGrid.FIRST_CELL_HEIGHT - 1)
    textobject.textLine('КПП')

    textobject.setTextOrigin(LEFT_TEXT_POSITION, TOP - FONT_SIZE - UpperGrid.FIRST_CELL_HEIGHT - UpperGrid.INN_HEIGHT - 1)
    textobject.textLine('ИП Усольцев Александр Сергеевич')
    
    textobject.setTextOrigin(LEFT_TEXT_POSITION + UpperGrid.FIRST_CELL_WIDTH, TOP - FONT_SIZE)
    textobject.textLine('БИК')

    textobject.setTextOrigin(RIGHT - UpperGrid.QR_CODE_WIDTH - UpperGrid.ACCOUNT_WIDTH + 2, TOP - FONT_SIZE)
    textobject.textLine('044525411')

    textobject.setTextOrigin(LEFT_TEXT_POSITION + UpperGrid.FIRST_CELL_WIDTH, TOP - FONT_SIZE - UpperGrid.INN_HEIGHT)
    textobject.textLine('Сч. №')

    textobject.setTextOrigin(RIGHT - UpperGrid.QR_CODE_WIDTH - UpperGrid.ACCOUNT_WIDTH + 2, TOP - FONT_SIZE - UpperGrid.INN_HEIGHT)
    textobject.textLine('30101810145250000411')

    textobject.setTextOrigin(LEFT_TEXT_POSITION + UpperGrid.FIRST_CELL_WIDTH, TOP - FONT_SIZE - UpperGrid.FIRST_CELL_HEIGHT)
    textobject.textLine('Сч. №')

    textobject.setTextOrigin(RIGHT - UpperGrid.QR_CODE_WIDTH - UpperGrid.ACCOUNT_WIDTH + 2, TOP - FONT_SIZE - UpperGrid.FIRST_CELL_HEIGHT)
    textobject.textLine('40802810113540000654')

    
    SMALL_FONT_SIZE = 8
    textobject.setFont('Arial', SMALL_FONT_SIZE)
    textobject.setTextOrigin(LEFT_TEXT_POSITION, TOP - UpperGrid.FIRST_CELL_HEIGHT + SMALL_FONT_SIZE/2)
    textobject.textLine('Банк получателя')

    textobject.setTextOrigin(LEFT_TEXT_POSITION, TOP - UpperGrid.HEIGHT + SMALL_FONT_SIZE/2)
    textobject.textLine('Получатель')

    textobject.setTextOrigin(RIGHT - UpperGrid.QR_CODE_WIDTH + 2, TOP - UpperGrid.HEIGHT + 2*SMALL_FONT_SIZE)
    textobject.textLine('Отсканируйте для')
    textobject.setTextOrigin(RIGHT - UpperGrid.QR_CODE_WIDTH + 2 + 20, TOP - UpperGrid.HEIGHT + 1*SMALL_FONT_SIZE - 2.5)
    textobject.textLine('оплаты')
    

    pdf.drawText(textobject)


def _print_header_text(pdf: canvas.Canvas) -> None: 
    textobject = pdf.beginText()
    textobject.setFont('BoldArial', Header.FONT_SIZE)

    textobject.setTextOrigin(LEFT + 4, Header.Y_POSITION)
    textobject.textLine(f'Счет на оплату № 1842 от {get_current_date_str()}')

    pdf.drawText(textobject)
    
    pdf.setLineWidth(1.1)
    pdf.line(LEFT, Header.Y_POSITION - 13, RIGHT, Header.Y_POSITION - 13)


def _print_contract_info(pdf: canvas.Canvas, order) -> None: 
    LEFT_TEXT_POSITION = LEFT + 2
    PARTNERS_LEFT = LEFT + 75
    CURRENT_FONT_SIZE = 9.8
    BLOCK_HEIGHT = 32
    MAX_CHARS_IN_LINE = 75

    textobject = pdf.beginText()
    textobject.setFont('Arial', CURRENT_FONT_SIZE) 

    textobject.setTextOrigin(LEFT_TEXT_POSITION, ContractInfoBlock.Y_POSITION)
    textobject.textLine('Поставщик')
    textobject.textLine('(Исполнитель):')

    textobject.setTextOrigin(LEFT_TEXT_POSITION, ContractInfoBlock.Y_POSITION - 1 * BLOCK_HEIGHT)
    textobject.textLine('Покупатель')
    textobject.textLine('(Заказчик):')

    textobject.setTextOrigin(LEFT_TEXT_POSITION, ContractInfoBlock.Y_POSITION - 2 * BLOCK_HEIGHT)
    textobject.textLine('Основание:')
    
    textobject.setFont('BoldArial', CURRENT_FONT_SIZE)

    provider_info = 'ИП Усольцев А.С., ИНН 250999742802, 692852, Приморский край, Партизанск г, Партизанская ул, дом 112, квартира 57'
    result_lines = split_text_into_lines(text=provider_info, max_chars_in_line=MAX_CHARS_IN_LINE)
    textobject.setTextOrigin(PARTNERS_LEFT, TOP - UpperGrid.HEIGHT - Header.HEIGHT)
    for line in result_lines: 
        textobject.textLine(line)


    customer_info = 'ИП Шубина Валентина Павловна, ИНН 940200030436, 291011, Луганская Народная респ., г Луганск, ул. Советская, д. 92А, кв. 465'
    customer_info = ''
    customer_info = f'{order.user.organization_name}, ИНН {order.user.inn}, {order.user.full_address}'
    result_lines = split_text_into_lines(text=customer_info, max_chars_in_line=MAX_CHARS_IN_LINE)
    textobject.setTextOrigin(PARTNERS_LEFT, TOP - UpperGrid.HEIGHT - Header.HEIGHT - 1 * BLOCK_HEIGHT)
    for line in result_lines: 
        textobject.textLine(line)


    textobject.setTextOrigin(PARTNERS_LEFT, TOP - UpperGrid.HEIGHT - Header.HEIGHT - 2 * BLOCK_HEIGHT)
    textobject.textLine('Основной договор')

    pdf.drawText(textobject)


def _print_items_grid(pdf: canvas.Canvas, items: Iterable) -> None: 
    pdf.setLineWidth(1.2)
    table_height = ItemsTable.get_height(len(items))
    outer_table_lines = [
        (LEFT, ItemsTable.Y_POSITION, RIGHT, ItemsTable.Y_POSITION), 
        (RIGHT, ItemsTable.Y_POSITION, RIGHT, ItemsTable.Y_POSITION - table_height),
        (LEFT, ItemsTable.Y_POSITION, LEFT, ItemsTable.Y_POSITION - table_height), 
        (LEFT, ItemsTable.Y_POSITION - table_height, RIGHT, ItemsTable.Y_POSITION - table_height),    
    ]
    pdf.lines(outer_table_lines)

    pdf.setLineWidth(0.6)
    inner_table_lines = [
        (ItemsTable.NUMBER_COLUMN_X_POS, ItemsTable.Y_POSITION, ItemsTable.NUMBER_COLUMN_X_POS, ItemsTable.Y_POSITION - table_height), 
        (ItemsTable.NAME_COLUMN_X_POS, ItemsTable.Y_POSITION, ItemsTable.NAME_COLUMN_X_POS, ItemsTable.Y_POSITION - table_height), 
        (ItemsTable.QUANTITY_COLUMN_X_POS, ItemsTable.Y_POSITION, ItemsTable.QUANTITY_COLUMN_X_POS, ItemsTable.Y_POSITION - table_height), 
        (ItemsTable.MEASURE_COLUMN_X_POS, ItemsTable.Y_POSITION, ItemsTable.MEASURE_COLUMN_X_POS, ItemsTable.Y_POSITION - table_height), 
        (ItemsTable.PRICE_COLUMN_X_POS, ItemsTable.Y_POSITION, ItemsTable.PRICE_COLUMN_X_POS, ItemsTable.Y_POSITION - table_height), 
        (ItemsTable.TOTAL_PRICE_COLUMN_X_POS, ItemsTable.Y_POSITION, ItemsTable.TOTAL_PRICE_COLUMN_X_POS, ItemsTable.Y_POSITION - table_height)
    ]
    for i in range(len(items)): 
        inner_table_lines.append((
            LEFT, 
            ItemsTable.Y_POSITION - (ItemsTable.HEADER_HEIGHT + i * ItemsTable.ROW_HEIGHT), 
            RIGHT, 
            ItemsTable.Y_POSITION - (ItemsTable.HEADER_HEIGHT + i * ItemsTable.ROW_HEIGHT), 
        ))
    pdf.lines(inner_table_lines)


def _print_items_grid_header_text(pdf: canvas.Canvas) -> None: 
    textobject = pdf.beginText()
    CURRENT_FONT_SIZE = 10
    margin_top = 10
    textobject.setFont('BoldArial', CURRENT_FONT_SIZE)

    textobject.setTextOrigin(LEFT + 8, ItemsTable.Y_POSITION - margin_top)
    textobject.textLine('№')

    textobject.setTextOrigin(ItemsTable.NAME_COLUMN_X_POS + 64, ItemsTable.Y_POSITION - margin_top)
    textobject.textLine('Товары (работы, услуги)')

    textobject.setTextOrigin(ItemsTable.QUANTITY_COLUMN_X_POS + 5, ItemsTable.Y_POSITION - margin_top)
    textobject.textLine('Кол-во')

    textobject.setTextOrigin(ItemsTable.MEASURE_COLUMN_X_POS + 7, ItemsTable.Y_POSITION - margin_top)
    textobject.textLine('Ед.')

    textobject.setTextOrigin(ItemsTable.PRICE_COLUMN_X_POS + 16, ItemsTable.Y_POSITION - margin_top)
    textobject.textLine('Цена')

    textobject.setTextOrigin(ItemsTable.TOTAL_PRICE_COLUMN_X_POS + 25, ItemsTable.Y_POSITION - margin_top)
    textobject.textLine('Сумма')

    pdf.drawText(textobject)
    

def _print_items_grid_text(pdf: canvas.Canvas, items: Iterable) -> None: 
    textobject = pdf.beginText()
    SMALL_FONT_SIZE = 8
    textobject.setFont('Arial', SMALL_FONT_SIZE)
    margin_top = 8.5
    MAX_CHARS_IN_LINE = 64

    print(items)

    for i, item in enumerate(items): 
        row_y_pos = ItemsTable.Y_POSITION - ItemsTable.HEADER_HEIGHT - ItemsTable.ROW_HEIGHT * i - margin_top
        textobject.setTextOrigin(LEFT + 8, row_y_pos)
        textobject.textLine(str(i + 1))

        print(i)
        print(item)

        textobject.setTextOrigin(ItemsTable.NAME_COLUMN_X_POS + 2, row_y_pos)
        for line in split_text_into_lines(item.product_name, MAX_CHARS_IN_LINE): 
            textobject.textLine(line)
        
        textobject.setTextOrigin(ItemsTable.QUANTITY_COLUMN_X_POS + 2, row_y_pos)
        textobject.textLine(str(item.quantity))

        textobject.setTextOrigin(ItemsTable.MEASURE_COLUMN_X_POS + 2, row_y_pos)
        textobject.textLine('шт')

        textobject.setTextOrigin(ItemsTable.MEASURE_COLUMN_X_POS + 2, row_y_pos)
        textobject.textLine('шт')

        textobject.setTextOrigin(ItemsTable.PRICE_COLUMN_X_POS + 2, row_y_pos)
        textobject.textLine(str(item.unit_price))

        textobject.setTextOrigin(ItemsTable.TOTAL_PRICE_COLUMN_X_POS + 2, row_y_pos)
        textobject.textLine(str(item.total_price))

    pdf.drawText(textobject)


def _print_total_price_text(pdf: canvas.Canvas, order, items) -> None: 
    CURRENT_FONT_SIZE = 10
    LINE_HEIGHT = 13
    table_height = ItemsTable.get_height(len(items))
    pdf.setFont('BoldArial', CURRENT_FONT_SIZE)

    first_line_y = ItemsTable.Y_POSITION - table_height - ItemsTable.MARGIN_BOTTOM 
    second_line_y = ItemsTable.Y_POSITION - table_height - ItemsTable.MARGIN_BOTTOM - 1 * LINE_HEIGHT
    third_line_y = ItemsTable.Y_POSITION - table_height - ItemsTable.MARGIN_BOTTOM - 2 * LINE_HEIGHT

    total_price_str = get_formatted_price(order.total_price)

    pdf.drawString(
        x = ItemsTable.TOTAL_PRICE_COLUMN_X_POS - pdf.stringWidth('Итого:'), 
        y = first_line_y, 
        text = 'Итого:'
    )
    pdf.drawString(
        x = ItemsTable.TOTAL_PRICE_COLUMN_X_POS - pdf.stringWidth('Без налога (НДС)'), 
        y = second_line_y, 
        text = 'Без налога (НДС)'
    )
    pdf.drawString(
        x = ItemsTable.TOTAL_PRICE_COLUMN_X_POS - pdf.stringWidth('Всего к оплате:'), 
        y = third_line_y, 
        text = 'Всего к оплате:'
    )

    margin_right = 6
    pdf.drawString(
        x = RIGHT - pdf.stringWidth(total_price_str) - margin_right, 
        y = first_line_y, 
        text = total_price_str
    )
    pdf.drawString(
        x = RIGHT - pdf.stringWidth('-') - margin_right, 
        y = second_line_y, 
        text = '-'
    )
    pdf.drawString(
        x = RIGHT - pdf.stringWidth(total_price_str) - margin_right, 
        y = third_line_y, 
        text = total_price_str
    )


def _print_bottom_text(pdf: canvas.Canvas, order, items) -> None: 
    CURRENT_FONT_SIZE = 10
    bottom_text_y_pos = BottomText.get_y_position(len(items))
    textobject = pdf.beginText()
    
    textobject.setFont('Arial', CURRENT_FONT_SIZE) 
    textobject.setTextOrigin(LEFT, bottom_text_y_pos)
    textobject.textLine(f'Всего наименований {len(items)}, на сумму {get_formatted_price(order.total_price)} руб.')

    textobject.setFont('BoldArial', CURRENT_FONT_SIZE) 
    textobject.textLine(convert_price_to_words(order.total_price))

    textobject.setFont('Arial', FONT_SIZE)
    textobject.setTextOrigin(LEFT, bottom_text_y_pos - 32)
    textobject.textLine(f'Оплатить не позднее {(datetime.now() + timedelta(days=5)).strftime("%d.%m.%Y")}')

    textobject.textLine('Внимание! В назначении платежа просим указать: Оплата по сч. № _____ от _________________ (дата) за')
    textobject.textLine('косметические товары.')
    
    divider_line_y = bottom_text_y_pos - 66

    pdf.setLineWidth(1.4)
    pdf.line(LEFT, divider_line_y, RIGHT, divider_line_y)

    bottom_label_y_pos = divider_line_y - 32
    textobject.setTextOrigin(LEFT, bottom_label_y_pos)
    textobject.setFont('BoldArial', CURRENT_FONT_SIZE)
    textobject.textLine('Предприниматель')

    pdf.setLineWidth(0.6)
    pdf.setFont('BoldArial', CURRENT_FONT_SIZE)
    pdf.line(LEFT + pdf.stringWidth('Предприниматель '), bottom_label_y_pos, RIGHT, bottom_label_y_pos)

    textobject.setTextOrigin(LEFT + 425, bottom_label_y_pos + 4)
    textobject.setFont('Arial', FONT_SIZE)
    textobject.textLine('Усольцев А. С.')

    pdf.drawText(textobject)




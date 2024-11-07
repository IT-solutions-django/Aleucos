from datetime import datetime
from num2words import num2words
from .config import * 


def split_text_into_lines(text: str, max_chars_in_line: int) -> list[str]:
    result_lines = []
    line = ''
    
    for word in text.split():
        if line:
            line += ' ' + word
        else:
            line = word
        
        if len(line) > max_chars_in_line:
            result_lines.append(line[:-len(word)].strip())
            line = word
    
    if line:
        result_lines.append(line)
    
    return result_lines


def get_current_date_str() -> str: 
    now = datetime.now()
    date_str = f'{now.day} {MONTHS_MAPPER[now.month]} {now.year} г.' 
    return date_str


def get_formatted_price(price: float) -> str: 
    return f"{price:,.2f}".replace(",", " ").replace(".", ",")


def convert_price_to_words(price: float) -> str: 
    rubles = int(price)
    kopecks = round((price - rubles) * 100)
    
    rubles_text = num2words(rubles, lang='ru').capitalize()
    
    return f"{rubles_text} рубля {kopecks} копейки"

# api_ruonia.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from config import logger

def get_ruonia_rate():
    """Получает ставку RUONIA с сайта ЦБ РФ"""
    try:
        url = "https://cbr.ru/hd_base/ruonia/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        logger.info(f"Запрос к URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            logger.error(f"Ошибка HTTP {response.status_code} при парсинге RUONIA")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        logger.info("HTML получен успешно")

        # Ищем таблицу со ставками RUONIA - пробуем разные селекторы
        table = soup.find('table', class_='data')
        if not table:
            table = soup.find('table')
            logger.info("Таблица найдена без класса")

        if table:
            logger.info("Таблица найдена, начинаем парсинг строк")
            rows = table.find_all('tr')
            logger.info(f"Найдено строк в таблице: {len(rows)}")

            # Пропускаем заголовок и ищем данные
            for i, row in enumerate(rows[1:], 1):  # Пропускаем заголовок
                cells = row.find_all(['td', 'th'])
                logger.info(f"Строка {i}: {len(cells)} ячеек")

                if len(cells) >= 2:
                    # Пытаемся получить дату и ставку из разных ячеек
                    date_str = None
                    rate_str = None

                    # Пробуем разные варианты структуры таблицы
                    for j, cell in enumerate(cells):
                        text = cell.get_text(strip=True)
                        logger.info(f"  Ячейка {j}: '{text}'")

                        # Проверяем, является ли текст датой
                        if not date_str and is_date(text):
                            date_str = text
                        # Проверяем, является ли текст числом (ставкой)
                        elif not rate_str and is_rate(text):
                            rate_str = text

                    logger.info(f"Найдено: дата='{date_str}', ставка='{rate_str}'")

                    if date_str and rate_str:
                        try:
                            date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                            # Берем последнюю доступную ставку (не из будущего)
                            if date_obj <= datetime.now():
                                rate_value = float(rate_str.replace(',', '.'))

                                logger.info(f"Успешно получена ставка RUONIA: {rate_value}% на {date_str}")

                                return {
                                    'rate': rate_value,
                                    'date': date_obj.strftime('%d.%m.%Y'),
                                    'is_current': True,
                                    'source': 'cbr_parsed'
                                }
                        except ValueError as e:
                            logger.warning(f"Ошибка преобразования данных: {e}")
                            continue

            logger.error("Не удалось найти валидные данные в таблице")
        else:
            logger.error("Таблица не найдена на странице")

        return None

    except Exception as e:
        logger.error(f"Ошибка при получении ставки RUONIA: {e}")
        return None

def is_date(text):
    """Проверяет, является ли текст датой в формате DD.MM.YYYY"""
    try:
        if text and len(text) == 10 and text[2] == '.' and text[5] == '.':
            datetime.strptime(text, '%d.%m.%Y')
            return True
    except:
        pass
    return False

def is_rate(text):
    """Проверяет, является ли текст числом (ставкой)"""
    try:
        if text and text.replace(',', '').replace('.', '').isdigit():
            # Проверяем, что это разумное значение ставки (от 1 до 30%)
            value = float(text.replace(',', '.'))
            return 1 <= value <= 30
    except:
        pass
    return False

def format_ruonia_message(ruonia_data: dict) -> str:
    """Форматирует сообщение со ставкой RUONIA"""
    if not ruonia_data:
        return "❌ Не удалось получить данные по ставке RUONIA от ЦБ РФ."

    rate = ruonia_data['rate']
    source = ruonia_data.get('source', 'unknown')

    message = f"📊 <b>СТАВКА RUONIA</b>\n\n"
    message += f"<b>Текущее значение:</b> {rate:.2f}%\n"
    message += f"<b>Дата:</b> {ruonia_data.get('date', 'неизвестно')}\n\n"
    message += "💡 <i>RUONIA (Ruble Overnight Index Average) - индикативная ставка overnight-кредитов в рублях</i>"

    # Добавляем информацию об источнике данных
    if source == 'cbr_parsed':
        message += f"\n\n✅ <i>Данные получены с официального сайта ЦБ РФ</i>"

    return message
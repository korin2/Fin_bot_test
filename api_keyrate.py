import logging
from datetime import datetime
from config import logger
# Импортируем нашу новую функцию из api_currency
from api_currency import get_key_rate_cbr

def get_key_rate():
    """Получает ключевую ставку ЦБ РФ с использованием cbrapi"""
    try:
        # Пробуем получить через cbrapi
        key_rate_data = get_key_rate_cbr()
        if key_rate_data:
            logger.info(f"Ключевая ставка получена через cbrapi: {key_rate_data['rate']}%")
            return key_rate_data

        # Если не получилось, пробуем старые методы как fallback
        logger.info("cbrapi не сработал, пробуем HTML парсинг...")
        key_rate_data = get_key_rate_html()
        if key_rate_data:
            return key_rate_data

        logger.info("Парсинг HTML не удался, пробуем API...")
        key_rate_data = get_key_rate_api()
        if key_rate_data:
            return key_rate_data

        # Если все методы не сработали, возвращаем демо-данные
        logger.warning("Не удалось получить актуальную ключевую ставку, используем демо-данные")
        return get_key_rate_demo()

    except Exception as e:
        logger.error(f"Ошибка при получении ключевой ставки: {e}")
        return get_key_rate_demo()

def get_key_rate_html():
    """Парсинг ключевой ставки с сайта ЦБ РФ (fallback)"""
    try:
        import requests
        from bs4 import BeautifulSoup

        url = "https://cbr.ru/hd_base/KeyRate/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.cbr.ru/',
            'Connection': 'keep-alive',
        }

        # Добавляем задержку чтобы не выглядеть как бот
        import time
        time.sleep(1)

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 403:
            logger.error("Доступ запрещен (403) при парсинге HTML")
            return None
        elif response.status_code != 200:
            logger.error(f"Ошибка HTTP {response.status_code} при парсинге HTML")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Ищем таблицу с ключевыми ставками
        table = soup.find('table', class_='data')
        if table:
            rows = table.find_all('tr')
            for i in range(1, min(len(rows), 10)):  # Проверяем первые 10 строк
                cells = rows[i].find_all('td')
                if len(cells) >= 2:
                    date_str = cells[0].get_text(strip=True)
                    rate_str = cells[1].get_text(strip=True).replace(',', '.')

                    try:
                        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                        # Проверяем что дата не в будущем
                        if date_obj <= datetime.now():
                            rate_value = float(rate_str)

                            return {
                                'rate': rate_value,
                                'date': date_obj.strftime('%d.%m.%Y'),
                                'is_current': True,
                                'source': 'cbr_parsed'
                            }
                    except ValueError:
                        continue

        return None

    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML ключевой ставки: {e}")
        return None

def get_key_rate_api():
    """Получает ключевую ставку через API ЦБ РФ (fallback)"""
    try:
        import requests
        from bs4 import BeautifulSoup

        # Альтернативный URL для ключевой ставки
        url = "https://www.cbr.ru/hd_base/KeyRate/?UniDbQuery.Posted=True&UniDbQuery.From=01.01.2020&UniDbQuery.To=31.12.2025"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='data')

            if table:
                rows = table.find_all('tr')
                for i in range(1, min(len(rows), 5)):  # Первые 5 строк
                    cells = rows[i].find_all('td')
                    if len(cells) >= 2:
                        date_str = cells[0].get_text(strip=True)
                        rate_str = cells[1].get_text(strip=True).replace(',', '.')

                        try:
                            date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                            if date_obj <= datetime.now():
                                rate_value = float(rate_str)

                                return {
                                    'rate': rate_value,
                                    'date': date_str,
                                    'is_current': True,
                                    'source': 'cbr_api'
                                }
                        except ValueError:
                            continue
        return None

    except Exception as e:
        logger.error(f"Ошибка при получении ключевой ставки через API: {e}")
        return None

def get_key_rate_demo():
    """Возвращает демо-данные ключевой ставки"""
    return {
        'rate': 16.0,  # Примерное значение
        'date': datetime.now().strftime('%d.%m.%Y'),
        'is_current': True,
        'source': 'demo'
    }

def format_key_rate_message(key_rate_data: dict) -> str:
    """Форматирует сообщение с ключевой ставкой"""
    if not key_rate_data:
        return "❌ Не удалось получить данные по ключевой ставке от ЦБ РФ."

    rate = key_rate_data['rate']
    source = key_rate_data.get('source', 'unknown')

    message = f"💎 <b>КЛЮЧЕВАЯ СТАВКА ЦБ РФ</b>\n\n"
    message += f"<b>Текущее значение:</b> {rate:.2f}%\n"
    message += f"\n<b>Дата установления:</b> {key_rate_data.get('date', 'неизвестно')}\n\n"
    message += "💡 <i>Ключевая ставка - это основная процентная ставка ЦБ РФ,"
    message += "которая влияет на кредиты, депозиты и экономику в целом</i>"

    # Добавляем информацию об источнике данных
    if source == 'cbrapi':
        message += f"\n\n✅ <i>Данные получены через официальное API ЦБ РФ (cbrapi)</i>"
    elif source == 'cbr_parsed':
        message += f"\n\n✅ <i>Данные получены с официального сайта ЦБ РФ</i>"
    elif source == 'cbr_api':
        message += f"\n\n✅ <i>Данные получены через API ЦБ РФ</i>"
    elif source == 'demo':
        message += f"\n\n⚠️ <i>Используются демонстрационные данные (ошибка получения реальных)</i>"

    return message
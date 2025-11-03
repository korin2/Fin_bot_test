import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            logger.error(f"Ошибка HTTP {response.status_code} при получении RUONIA")
            return get_ruonia_demo()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Ищем таблицу со ставками RUONIA
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
                        # Берем самую последнюю дату, которая не в будущем
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

        return get_ruonia_demo()

    except Exception as e:
        logger.error(f"Ошибка при получении ставки RUONIA: {e}")
        return get_ruonia_demo()

def get_ruonia_demo():
    """Демо-данные RUONIA на случай недоступности API"""
    return {
        'rate': 15.5,  # Примерное значение
        'date': datetime.now().strftime('%d.%m.%Y'),
        'is_current': True,
        'source': 'demo'
    }

def format_ruonia_message(ruonia_data):
    """Форматирует сообщение со ставкой RUONIA"""
    if not ruonia_data:
        return "❌ Не удалось получить данные по ставке RUONIA."

    rate = ruonia_data['rate']

    message = (
        f"📊 <b>СТАВКА RUONIA</b>\n\n"
        f"<b>Текущее значение:</b> {rate:.2f}%\n"
        f"<b>Дата:</b> {ruonia_data.get('date', 'неизвестно')}\n\n"
        f"💡 <i>RUONIA (Ruble OverNight Index Average) - это средневзвешенная ставка по однодневным рублевым депозитам, размещаемым российскими банками</i>"
    )

    if ruonia_data.get('source') == 'demo':
        message += f"\n\n⚠️ <i>Используются демонстрационные данные (ошибка получения реальных)</i>"

    return message
# api_ruonia.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
from config import logger
from smart_cache import cache_manager

def get_ruonia_rate(use_cache=True):
    """Получает ставку RUONIA с сайта ЦБ РФ с поддержкой кэширования"""
    if use_cache:
        return cache_manager.get_data('ruonia', _get_ruonia_rate_impl)
    else:
        return _get_ruonia_rate_impl()

def _get_ruonia_rate_impl():
    """Реальная реализация парсинга RUONIA (перенесена из старой get_ruonia_rate)"""
    try:
        url = "https://cbr.ru/hd_base/ruonia/dynamics/"
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

        # ... (остальной код парсинга без изменений)
        table = soup.find('table', class_='data')
        if not table:
            table = soup.find('table')
            logger.info("Таблица найдена без класса")

        if table:
            logger.info("Таблица найдена, начинаем парсинг строк")
            rows = table.find_all('tr')
            logger.info(f"Найдено строк в таблице: {len(rows)}")

            rates_data = []
            for i, row in enumerate(rows[1:], 1):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    try:
                        date_text = cells[0].get_text(strip=True)
                        rate_text = cells[1].get_text(strip=True)
                        date_obj = datetime.strptime(date_text, '%d.%m.%Y')
                        rate_value = float(rate_text.replace(',', '.'))

                        if date_obj <= datetime.now() and 1 <= rate_value <= 30:
                            rates_data.append({
                                'date': date_obj,
                                'rate': rate_value,
                                'date_str': date_text
                            })
                            logger.info(f"Найдена ставка: {date_text} - {rate_value}%")

                    except (ValueError, IndexError) as e:
                        logger.warning(f"Ошибка парсинга строки {i}: {e}")
                        continue

            if rates_data:
                rates_data.sort(key=lambda x: x['date'], reverse=True)
                latest_rate = rates_data[0]
                logger.info(f"Самая свежая ставка: {latest_rate['date_str']} - {latest_rate['rate']}%")

                return {
                    'rate': latest_rate['rate'],
                    'date': latest_rate['date_str'],
                    'is_current': True,
                    'source': 'cbr_parsed'
                }
            else:
                logger.error("Не найдено валидных данных в таблице")
        else:
            logger.error("Таблица не найдена на странице")

        return None

    except Exception as e:
        logger.error(f"Ошибка при получении ставки RUONIA: {e}")
        return None

def get_ruonia_historical(days=30, use_cache=True):
    """Получает исторические данные RUONIA за указанное количество дней с кэшированием"""
    if use_cache:
        cache_key = f'ruonia_historical_{days}'
        return cache_manager.get_data(cache_key, lambda: _get_ruonia_historical_impl(days))
    else:
        return _get_ruonia_historical_impl(days)

def _get_ruonia_historical_impl(days=30):
    """Реальная реализация получения исторических данных"""
    # ... (код из старой get_ruonia_historical без изменений)
    try:
        url = "https://cbr.ru/hd_base/ruonia/dynamics/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        }

        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', class_='data')
        if not table:
            table = soup.find('table')

        if table:
            rates_data = []
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    try:
                        date_text = cells[0].get_text(strip=True)
                        rate_text = cells[1].get_text(strip=True)
                        date_obj = datetime.strptime(date_text, '%d.%m.%Y')
                        rate_value = float(rate_text.replace(',', '.'))

                        if date_obj <= datetime.now() and 1 <= rate_value <= 30:
                            rates_data.append({
                                'date': date_obj,
                                'rate': rate_value,
                                'date_str': date_text
                            })
                    except (ValueError, IndexError):
                        continue

            rates_data.sort(key=lambda x: x['date'], reverse=True)
            return rates_data[:days]

        return None

    except Exception as e:
        logger.error(f"Ошибка при получении исторических данных RUONIA: {e}")
        return None


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

def format_ruonia_historical_message(historical_data: list) -> str:
    """Форматирует сообщение с историческими данными RUONIA"""
    if not historical_data:
        return "❌ Не удалось получить исторические данные по ставке RUONIA."

    message = "📈 <b>ИСТОРИЯ СТАВКИ RUONIA</b>\n\n"

    # Показываем последние 10 записей
    for i, data in enumerate(historical_data[:10]):
        date_str = data['date_str']
        rate = data['rate']

        # Добавляем эмодзи для визуального отличия
        if i == 0:
            indicator = "🟢"  # Самая свежая
        elif i < 3:
            indicator = "🔵"  # Недавние
        else:
            indicator = "⚪"  # Более старые

        message += f"{indicator} <b>{date_str}:</b> {rate:.2f}%\n"

    # Добавляем статистику
    if len(historical_data) > 1:
        rates = [data['rate'] for data in historical_data]
        current_rate = rates[0]
        previous_rate = rates[1] if len(rates) > 1 else current_rate
        change = current_rate - previous_rate
        change_percent = (change / previous_rate) * 100 if previous_rate > 0 else 0

        change_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"

        message += f"\n📊 <b>Изменение за день:</b> {change_icon} {change:+.2f}% ({change_percent:+.2f}%)\n"

    message += f"\n📅 <i>Показано последних {min(10, len(historical_data))} из {len(historical_data)} записей</i>\n"
    message += "✅ <i>Данные с официального сайта ЦБ РФ</i>"

    return message
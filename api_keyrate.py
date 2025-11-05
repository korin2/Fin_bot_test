# api_keyrate.py - обновляем функции с кэшированием
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from config import logger

# 🔄 ДОБАВЛЯЕМ ИМПОРТ ДЛЯ КЭШИРОВАНИЯ
from cache import get_cache, set_cache

def get_key_rate():
    """Получает ключевую ставку ЦБ РФ с использованием нескольких методов И КЭШИРОВАНИЯ"""
    try:
        # 🎯 ПРОВЕРЯЕМ КЭШ ПЕРВЫМ ДЕЛОМ
        cache_key = "key_rate"
        cached_data = get_cache(cache_key)
        
        # ✅ ЕСЛИ ДАННЫЕ ЕСТЬ В КЭШЕ - ВОЗВРАЩАЕМ ИХ
        if cached_data:
            logger.info("💾 Используются кэшированные данные ключевой ставки")
            return cached_data
        
        # 🔄 ЕСЛИ ДАННЫХ НЕТ В КЭШЕ - ЗАПРАШИВАЕМ У API
        logger.info("🌐 Запрашиваем свежие данные ключевой ставки у ЦБ РФ")

        # Сначала пробуем парсинг HTML с правильными заголовками
        key_rate_data = get_key_rate_html()
        if key_rate_data:
            # 💾 СОХРАНЯЕМ В КЭШ ПРИ УСПЕШНОМ ПОЛУЧЕНИИ
            set_cache(cache_key, key_rate_data)
            logger.info("💾 Данные ключевой ставки сохранены в кэш на 24 часа")
            return key_rate_data

        # Если не получилось, пробуем API
        logger.info("Парсинг HTML не удался, пробуем API...")
        key_rate_data = get_key_rate_api()
        if key_rate_data:
            # 💾 СОХРАНЯЕМ В КЭШ ПРИ УСПЕШНОМ ПОЛУЧЕНИИ
            set_cache(cache_key, key_rate_data)
            logger.info("💾 Данные ключевой ставки сохранены в кэш на 24 часа")
            return key_rate_data

        # Если оба метода не сработали, возвращаем None вместо демо-данных
        logger.error("Не удалось получить актуальную ключевую ставку")
        return None

    except Exception as e:
        logger.error(f"Ошибка при получении ключевой ставки: {e}")
        return None

def get_key_rate_html():
    """Парсинг ключевой ставки с сайта ЦБ РФ"""
    try:
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
    """Получает ключевую ставку через API ЦБ РФ"""
    try:
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
    if source == 'cbr_parsed':
        message += f"\n\n✅ <i>Данные получены с официального сайта ЦБ РФ</i>"
    elif source == 'cbr_api':
        message += f"\n\n✅ <i>Данные получены через API ЦБ РФ</i>"
    
    # 🔄 ДОБАВЛЯЕМ ИНФОРМАЦИЮ О КЭШИРОВАНИИ
    message += f"\n\n💾 <i>Данные обновляются каждые 24 часа</i>"

    return message

def format_combined_rates_message(key_rate_data: dict, ruonia_data: dict = None) -> str:
    """Форматирует комбинированное сообщение с ключевой ставкой и RUONIA"""
    if not key_rate_data:
        return "❌ Не удалось получить данные по ключевой ставке от ЦБ РФ."

    key_rate = key_rate_data['rate']
    key_source = key_rate_data.get('source', 'unknown')

    message = "🏛️ <b>Ставки Банка России</b>\n\n"
    # Ключевая ставка
    message += "📊 <b>Ключевая ставка:</b>\n"
    message += f"Текущее значение: <b>{key_rate:.2f}%</b>\n"
    message += f"Дата: {key_rate_data.get('date', 'неизвестно')}\n\n"

    # Добавляем информацию о RUONIA если есть
    if ruonia_data:
        ruonia_rate = ruonia_data['rate']
        ruonia_source = ruonia_data.get('source', 'unknown')

        message += "📊 <b>СТАВКА RUONIA</b>\n"
        message += f"<b>Текущее значение:</b> {ruonia_rate:.2f}%\n"
        message += f"<b>Дата:</b> {ruonia_data.get('date', 'неизвестно')}\n\n"
        message += "   История ставки RUONIA - /ruonia_history\n\n"

        # Сравниваем ставки
        difference = key_rate - ruonia_rate
        if difference > 0:
            comparison = f"Ключевая ставка выше RUONIA на {difference:.2f}%"
        elif difference < 0:
            comparison = f"Ключевая ставка ниже RUONIA на {abs(difference):.2f}%"
        else:
            comparison = "Ставки равны"

        message += f"📈 <b>Сравнение:</b> {comparison}\n\n"
    else:
        message += "📊 <b>СТАВКА RUONIA:</b> ❌ данные временно недоступны\n\n"
        message += "   История ставки RUONIA - /ruonia_history\n\n"

    # Объяснение
    message += "💡 <b>Объяснение:</b>\n"
    message += "• <b>Ключевая ставка</b> - основная процентная ставка ЦБ РФ, которая влияет на кредиты, депозиты и экономику в целом;\n"

    if ruonia_data:
        message += "• <b>RUONIA</b> - индикативная ставка overnight-кредитов в рублях, отражает реальную стоимость денег на рынке\n\n"
        message += "📈 <i>Разница между ставками показывает настроения на денежном рынке.</i>"
    else:
        message += "• <b>RUONIA</b> - индикативная ставка overnight-кредитов в рублях\n\n"
        message += "📈 <i>Сравнение ставок временно недоступно</i>"

    # Добавляем информацию об источниках данных
    sources_info = "\n\n✅ <b>Источники данных:</b>\n"

    if key_source == 'cbr_parsed':
        sources_info += "• Ключевая ставка: официальный сайт ЦБ РФ\n"
    elif key_source == 'cbr_api':
        sources_info += "• Ключевая ставка: API ЦБ РФ\n"

    if ruonia_data:
        ruonia_source = ruonia_data.get('source', 'unknown')
        if ruonia_source == 'cbr_parsed':
            sources_info += "• RUONIA: официальный сайт ЦБ РФ\n"

    message += sources_info
    
    # 🔄 ДОБАВЛЯЕМ ИНФОРМАЦИЮ О КЭШИРОВАНИИ
    message += f"\n\n💾 <i>Данные обновляются каждые 24 часа</i>"

    return message

# 🔧 ДОБАВЛЯЕМ ФУНКЦИЮ ПРИНУДИТЕЛЬНОГО ОБНОВЛЕНИЯ
def refresh_keyrate_cache():
    """Принудительно обновляет кэш ключевой ставки"""
    try:
        from cache import force_refresh_cache
        
        # Очищаем кэш для ключевой ставки
        force_refresh_cache("key_rate")
        
        logger.info("🔄 Кэш ключевой ставки принудительно обновлен")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша ключевой ставки: {e}")
        return False

# api_ruonia.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
from config import logger

# 🔄 ДОБАВЛЯЕМ ИМПОРТ ДЛЯ КЭШИРОВАНИЯ
from cache import get_cache, set_cache

def get_ruonia_rate():
    """Получает ставку RUONIA с сайта ЦБ РФ (страница dynamics) С КЭШИРОВАНИЕМ"""
    try:
        # 🎯 ПРОВЕРЯЕМ КЭШ ПЕРВЫМ ДЕЛОМ
        cache_key = "ruonia_rate"
        cached_data = get_cache(cache_key)
        
        # ✅ ЕСЛИ ДАННЫЕ ЕСТЬ В КЭШЕ - ВОЗВРАЩАЕМ ИХ
        if cached_data:
            logger.info("💾 Используются кэшированные данные RUONIA")
            return cached_data
        
        # 🔄 ЕСЛИ ДАННЫХ НЕТ В КЭШЕ - ЗАПРАШИВАЕМ У API
        logger.info("🌐 Запрашиваем свежие данные RUONIA у ЦБ РФ")
        
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

        # Ищем таблицу со ставками RUONIA
        table = soup.find('table', class_='data')

        if not table:
            # Пробуем найти любую таблицу
            table = soup.find('table')
            logger.info("Таблица найдена без класса")

        if table:
            logger.info("Таблица найдена, начинаем парсинг строк")
            rows = table.find_all('tr')
            logger.info(f"Найдено строк в таблице: {len(rows)}")

            # Собираем все доступные данные
            rates_data = []

            for i, row in enumerate(rows[1:], 1):  # Пропускаем заголовок
                cells = row.find_all(['td', 'th'])

                if len(cells) >= 2:
                    try:
                        # Первая ячейка - дата
                        date_text = cells[0].get_text(strip=True)
                        # Вторая ячейка - ставка
                        rate_text = cells[1].get_text(strip=True)

                        # Парсим дату
                        date_obj = datetime.strptime(date_text, '%d.%m.%Y')

                        # Парсим ставку (заменяем запятую на точку)
                        rate_value = float(rate_text.replace(',', '.'))

                        # Проверяем, что дата не в будущем и ставка разумная
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

            # Сортируем по дате (от новых к старым) и берем самую свежую
            if rates_data:
                rates_data.sort(key=lambda x: x['date'], reverse=True)
                latest_rate = rates_data[0]

                logger.info(f"Самая свежая ставка: {latest_rate['date_str']} - {latest_rate['rate']}%")

                result = {
                    'rate': latest_rate['rate'],
                    'date': latest_rate['date_str'],
                    'is_current': True,
                    'source': 'cbr_parsed'
                }
                
                # 💾 СОХРАНЯЕМ РЕЗУЛЬТАТ В КЭШ
                set_cache(cache_key, result)
                logger.info("💾 Данные RUONIA сохранены в кэш на 24 часа")
                
                return result
            else:
                logger.error("Не найдено валидных данных в таблице")
        else:
            logger.error("Таблица не найдена на странице")

        return None

    except Exception as e:
        logger.error(f"Ошибка при получении ставки RUONIA: {e}")
        return None

def get_ruonia_historical(days=30):
    """Получает исторические данные RUONIA за указанное количество дней С КЭШИРОВАНИЕМ"""
    try:
        # 🎯 ПРОВЕРЯЕМ КЭШ ДЛЯ ИСТОРИЧЕСКИХ ДАННЫХ
        cache_key = f"ruonia_historical_{days}"
        cached_data = get_cache(cache_key)
        
        if cached_data:
            logger.info(f"💾 Используются кэшированные исторические данные RUONIA за {days} дней")
            return cached_data
        
        # 🔄 ЕСЛИ ДАННЫХ НЕТ В КЭШЕ - ЗАПРАШИВАЕМ У API
        logger.info(f"🌐 Запрашиваем свежие исторические данные RUONIA за {days} дней")

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

            for row in rows[1:]:  # Пропускаем заголовок
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

            # Сортируем по дате и ограничиваем количеством дней
            rates_data.sort(key=lambda x: x['date'], reverse=True)
            result = rates_data[:days]
            
            # 💾 СОХРАНЯЕМ РЕЗУЛЬТАТ В КЭШ
            set_cache(cache_key, result)
            logger.info(f"💾 Исторические данные RUONIA сохранены в кэш на 24 часа")
            
            return result

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
    
    # 🔄 ДОБАВЛЯЕМ ИНФОРМАЦИЮ О КЭШИРОВАНИИ
    message += f"\n\n💾 <i>Данные обновляются каждые 24 часа</i>"

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
    
    # 🔄 ДОБАВЛЯЕМ ИНФОРМАЦИЮ О КЭШИРОВАНИИ
    message += f"\n\n💾 <i>Данные обновляются каждые 24 часа</i>"

    return message

# 🔧 ДОБАВЛЯЕМ ФУНКЦИЮ ПРИНУДИТЕЛЬНОГО ОБНОВЛЕНИЯ
def refresh_ruonia_cache():
    """Принудительно обновляет кэш RUONIA"""
    try:
        from cache import force_refresh_cache
        
        # Очищаем кэш для RUONIA
        force_refresh_cache("ruonia_rate")
        force_refresh_cache("ruonia_historical_30")  # Очищаем кэш для 30 дней
        
        logger.info("🔄 Кэш RUONIA принудительно обновлен")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша RUONIA: {e}")
        return False

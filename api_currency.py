# api_currency.py
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
from config import CBR_API_BASE, logger

# 🔄 ДОБАВЛЯЕМ ИМПОРТ ДЛЯ КЭШИРОВАНИЯ
from cache import get_cache, set_cache

def get_currency_rates_for_date(date_req):
    """Получает курсы валют на определенную дату"""
    try:
        url = f"{CBR_API_BASE}scripts/XML_daily.asp"
        params = {'date_req': date_req}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None, None
        
        root = ET.fromstring(response.content)
        cbr_date = root.get('Date', '')
        
        rates = {}
        currency_codes = {
            'R01235': 'USD',  'R01239': 'EUR',  'R01035': 'GBP',  'R01820': 'JPY',
            'R01375': 'CNY',  'R01775': 'CHF',  'R01350': 'CAD',  'R01010': 'AUD',
            'R01700': 'TRY',  'R01335': 'KZT', 'R01230': 'AED',
        }
        
        for valute in root.findall('Valute'):
            valute_id = valute.get('ID')
            if valute_id in currency_codes:
                currency_code = currency_codes[valute_id]
                name = valute.find('Name').text
                value = float(valute.find('Value').text.replace(',', '.'))
                nominal = int(valute.find('Nominal').text)
                
                if nominal > 1:
                    value = value / nominal
                
                rates[currency_code] = {
                    'value': value,
                    'name': name,
                    'nominal': nominal
                }
        
        return rates, cbr_date
        
    except Exception as e:
        logger.error(f"Ошибка при получении курсов на дату {date_req}: {e}")
        return None, None

def get_currency_rates_with_history():
    """Получает курсы валют на сегодня, вчера и завтра (если доступно) С КЭШИРОВАНИЕМ"""
    try:
        # 🎯 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: ПРОВЕРЯЕМ КЭШ ПЕРВЫМ ДЕЛОМ
        cache_key = "currency_rates_with_history"
        cached_data = get_cache(cache_key)
        
        # ✅ ЕСЛИ ДАННЫЕ ЕСТЬ В КЭШЕ - ВОЗВРАЩАЕМ ИХ
        if cached_data:
            logger.info("💾 Используются кэшированные данные курсов валют")
            return cached_data
        
        # 🔄 ЕСЛИ ДАННЫХ НЕТ В КЭШЕ - ЗАПРАШИВАЕМ У API
        logger.info("🌐 Запрашиваем свежие данные курсов валют у ЦБ РФ")
        
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Форматируем даты для запроса
        date_today = today.strftime('%d/%m/%Y')
        date_yesterday = yesterday.strftime('%d/%m/%Y')
        date_tomorrow = tomorrow.strftime('%d/%m/%Y')
        
        # Получаем курсы на сегодня
        rates_today, date_today_str = get_currency_rates_for_date(date_today)
        if not rates_today:
            return {}, 'неизвестная дата', None, None, None, None
        
        # Получаем курсы на вчера
        rates_yesterday, date_yesterday_str = get_currency_rates_for_date(date_yesterday)
        
        # Пытаемся получить курсы на завтра
        rates_tomorrow, date_tomorrow_str = get_currency_rates_for_date(date_tomorrow)
        
        # Рассчитываем изменения по сравнению со вчера
        changes_yesterday = {}
        if rates_yesterday:
            for currency, today_data in rates_today.items():
                if currency in rates_yesterday:
                    today_value = today_data['value']
                    yesterday_value = rates_yesterday[currency]['value']
                    change = today_value - yesterday_value
                    change_percent = (change / yesterday_value) * 100 if yesterday_value > 0 else 0
                    
                    changes_yesterday[currency] = {
                        'change': change,
                        'change_percent': change_percent,
                        'yesterday_value': yesterday_value
                    }
        
        # Рассчитываем изменения для завтрашних курсов
        changes_tomorrow = {}
        if rates_tomorrow:
            for currency, today_data in rates_today.items():
                if currency in rates_tomorrow:
                    today_value = today_data['value']
                    tomorrow_value = rates_tomorrow[currency]['value']
                    change = tomorrow_value - today_value
                    change_percent = (change / today_value) * 100 if today_value > 0 else 0
                    
                    changes_tomorrow[currency] = {
                        'change': change,
                        'change_percent': change_percent,
                        'tomorrow_value': tomorrow_value
                    }
        
        # 📦 ФОРМИРУЕМ РЕЗУЛЬТАТ
        result = (
            rates_today, 
            date_today_str, 
            rates_yesterday, 
            changes_yesterday, 
            rates_tomorrow, 
            changes_tomorrow
        )
        
        # 💾 СОХРАНЯЕМ РЕЗУЛЬТАТ В КЭШ
        set_cache(cache_key, result)
        logger.info("💾 Данные курсов валют сохранены в кэш на 1 час")
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении курсов с историей: {e}")
        return {}, 'неизвестная дата', None, None, None, None

# 🔄 ОБНОВЛЯЕМ ФУНКЦИЮ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ
def get_currency_rates_with_tomorrow():
    """Совместимая функция для старых вызовов С КЭШИРОВАНИЕМ"""
    try:
        # 🎯 ТАКЖЕ ИСПОЛЬЗУЕМ КЭШИРОВАНИЕ
        cache_key = "currency_rates_tomorrow"
        cached_data = get_cache(cache_key)
        
        if cached_data:
            logger.info("💾 Используются кэшированные данные курсов (совместимость)")
            return cached_data
        
        # Получаем данные через основную функцию (которая уже кэшируется)
        rates_today, date_today, _, _, rates_tomorrow, changes_tomorrow = get_currency_rates_with_history()
        
        # Конвертируем changes_tomorrow в старый формат
        changes = {}
        if changes_tomorrow:
            for currency, change_info in changes_tomorrow.items():
                changes[currency] = {
                    'change': change_info['change'],
                    'change_percent': change_info['change_percent']
                }
        
        result = (rates_today, date_today, rates_tomorrow, changes)
        
        # Сохраняем в кэш
        set_cache(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка в совместимой функции: {e}")
        return {}, 'неизвестная дата', None, {}

# 🔧 ДОБАВЛЯЕМ ФУНКЦИЮ ПРИНУДИТЕЛЬНОГО ОБНОВЛЕНИЯ
def refresh_currency_cache():
    """Принудительно обновляет кэш курсов валют"""
    try:
        from cache import force_refresh_cache
        
        # Очищаем кэш для курсов валют
        force_refresh_cache("currency_rates_with_history")
        force_refresh_cache("currency_rates_tomorrow")
        
        logger.info("🔄 Кэш курсов валют принудительно обновлен")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша курсов: {e}")
        return False

# 📝 ОСТАВЛЯЕМ ФУНКЦИЮ ФОРМАТИРОВАНИЯ БЕЗ ИЗМЕНЕНИЙ
def format_currency_rates_message(rates_today: dict, date_today: str, 
                                rates_yesterday: dict = None, changes_yesterday: dict = None,
                                rates_tomorrow: dict = None, changes_tomorrow: dict = None) -> str:
    """Форматирует сообщение с курсами валют на сегодня, вчера и завтра"""
    if not rates_today:
        return "❌ Не удалось получить курсы валют от ЦБ РФ."
    
    message = f"💱 <b>КУРСЫ ВАЛЮТ ЦБ РФ</b>\n"
    message += f"📅 <i>на {date_today}</i>\n\n"
    
    # Основные валюты (доллар, евро)
    main_currencies = ['USD', 'EUR']
    for currency in main_currencies:
        if currency in rates_today:
            data = rates_today[currency]
            
            message += f"💵 <b>{data['name']}</b> ({currency}):\n"
            message += f"   <b>Сегодня: {data['value']:.2f} руб.</b>\n"
            
            # Показываем вчерашний курс и изменение
            if changes_yesterday and currency in changes_yesterday:
                change_info = changes_yesterday[currency]
                change_icon = "📈" if change_info['change'] > 0 else "📉" if change_info['change'] < 0 else "➡️"
                
                message += f"   <i>Вчера: {change_info['yesterday_value']:.2f} руб. {change_icon}</i>\n"
                message += f"   <i>Изменение: {change_info['change']:+.2f} руб. ({change_info['change_percent']:+.2f}%)</i>\n"
            
            # Показываем завтрашний курс если есть изменения
            if changes_tomorrow and currency in changes_tomorrow:
                change_info = changes_tomorrow[currency]
                change_icon = "📈" if change_info['change'] > 0 else "📉" if change_info['change'] < 0 else "➡️"
                
                message += f"   <i>Завтра: {change_info['tomorrow_value']:.2f} руб. {change_icon}</i>\n"
                message += f"   <i>Изменение: {change_info['change']:+.2f} руб. ({change_info['change_percent']:+.2f}%)</i>\n"
            elif rates_tomorrow and currency in rates_tomorrow:
                # Если курс на завтра есть, но изменений нет
                tomorrow_data = rates_tomorrow[currency]
                message += f"   <i>Завтра: {tomorrow_data['value']:.2f} руб. ➡️</i>\n"
            else:
                # Если курса на завтра нет
                message += f"   <i>Завтра: ЦБ РФ еще не установил курс</i>\n"
            
            message += "\n"
    
    # Другие валюты - AED будет первым в списке
    other_currencies = ['AED']
    other_currencies.extend([curr for curr in rates_today.keys() 
                           if curr not in main_currencies and curr != 'AED'])
    
    if other_currencies:
        message += "🌍 <b>Другие валюты:</b>\n"
        
        for currency in other_currencies:
            if currency in rates_today:
                data = rates_today[currency]
                
                # Для JPY показываем за 100 единиц
                if currency == 'JPY':
                    display_value = data['value'] * 100
                    currency_text = f"   {data['name']} ({currency}): <b>{display_value:.2f} руб.</b>"
                else:
                    currency_text = f"   {data['name']} ({currency}): <b>{data['value']:.2f} руб.</b>"
                
                # Добавляем индикатор изменения по сравнению со вчера
                if changes_yesterday and currency in changes_yesterday:
                    change_info = changes_yesterday[currency]
                    change_icon = "📈" if change_info['change'] > 0 else "📉" if change_info['change'] < 0 else "➡️"
                    currency_text += f" {change_icon}"
                
                message += currency_text + "\n"
    
    # Информация о доступности завтрашних курсов
    if rates_tomorrow:
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
        message += f"\n📊 <i>Курсы на завтра ({tomorrow_date}) опубликованы ЦБ РФ</i>"
    else:
        message += f"\n💡 <i>Курсы на завтра будут опубликованы ЦБ РФ позже</i>"
    
    # 🔄 ДОБАВЛЯЕМ ИНФОРМАЦИЮ О КЭШИРОВАНИИ
    message += f"\n\n💾 <i>Данные обновляются каждые 60 минут</i>"
    
    return message

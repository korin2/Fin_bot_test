import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
from config import CBR_API_BASE, logger

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

def get_currency_rates_with_tomorrow():
    """Получает курсы валют на сегодня и завтра (если доступно)"""
    try:
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        # Форматируем даты для запроса
        date_today = today.strftime('%d/%m/%Y')
        date_tomorrow = tomorrow.strftime('%d/%m/%Y')
        
        # Получаем курсы на сегодня
        rates_today, date_today_str = get_currency_rates_for_date(date_today)
        if not rates_today:
            return {}, 'неизвестная дата', None, None
        
        # Пытаемся получить курсы на завтра
        rates_tomorrow, date_tomorrow_str = get_currency_rates_for_date(date_tomorrow)
        
        # Если курсы на завтра не доступны, возвращаем только сегодняшние
        if not rates_tomorrow:
            return rates_today, date_today_str, None, None
        
        # Рассчитываем изменения для завтрашних курсов
        changes = {}
        for currency, today_data in rates_today.items():
            if currency in rates_tomorrow:
                today_value = today_data['value']
                tomorrow_value = rates_tomorrow[currency]['value']
                change = tomorrow_value - today_value
                change_percent = (change / today_value) * 100 if today_value > 0 else 0
                
                changes[currency] = {
                    'change': change,
                    'change_percent': change_percent
                }
        
        return rates_today, date_today_str, rates_tomorrow, changes
        
    except Exception as e:
        logger.error(f"Ошибка при получении курсов с завтрашними данными: {e}")
        return {}, 'неизвестная дата', None, None

def format_currency_rates_message(rates_today: dict, date_today: str, 
                                rates_tomorrow: dict = None, changes: dict = None) -> str:
    """Форматирует сообщение с курсами валют на сегодня и завтра"""
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
            message += f"   <b>{data['value']:.2f} руб.</b>\n"
            
            # Если есть данные на завтра, показываем прогноз
            if rates_tomorrow and currency in rates_tomorrow and currency in changes:
                tomorrow_data = rates_tomorrow[currency]
                change_info = changes[currency]
                change_icon = "📈" if change_info['change'] > 0 else "📉" if change_info['change'] < 0 else "➡️"
                
                message += f"   <i>Завтра: {tomorrow_data['value']:.2f} руб. {change_icon}</i>\n"
                message += f"   <i>Изменение: {change_info['change']:+.2f} руб. ({change_info['change_percent']:+.2f}%)</i>\n"
            
            message += "\n"
    
    # Другие валюты - AED будет первым в списке
    other_currencies = ['AED']  # Сначала AED
    other_currencies.extend([curr for curr in rates_today.keys() 
                           if curr not in main_currencies and curr != 'AED'])  # Затем остальные кроме AED
    
    if other_currencies:
        message += "🌍 <b>Другие валюты:</b>\n"
        
        for currency in other_currencies:
            if currency in rates_today:  # Проверяем наличие валюты
                data = rates_today[currency]
                
                # Для JPY показываем за 100 единиц
                if currency == 'JPY':
                    display_value = data['value'] * 100
                    currency_text = f"   {data['name']} ({currency}): <b>{display_value:.2f} руб.</b>"
                else:
                    currency_text = f"   {data['name']} ({currency}): <b>{data['value']:.2f} руб.</b>"
                
                # Добавляем индикатор изменения для завтра, если есть
                if rates_tomorrow and currency in rates_tomorrow and currency in changes:
                    change_info = changes[currency]
                    change_icon = "📈" if change_info['change'] > 0 else "📉" if change_info['change'] < 0 else "➡️"
                    currency_text += f" {change_icon}"
                
                message += currency_text + "\n"
    
    # Информация о доступности завтрашних курсов
    if rates_tomorrow:
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
        message += f"\n📊 <i>Курсы на завтра ({tomorrow_date}) опубликованы ЦБ РФ</i>"
    else:
        message += f"\n💡 <i>Курсы на завтра будут опубликованы ЦБ РФ позже</i>"
    
    message += f"\n\n💡 <i>Официальные курсы ЦБ РФ и актуальный на завтра</i>"
    return message

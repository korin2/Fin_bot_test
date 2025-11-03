import logging
from datetime import datetime, timedelta
from cbrapi import CbrApi
from config import logger

# Инициализируем клиент CBR API с настройками
cbr_client = CbrApi(
    timeout=10,
    retry_count=3,
    cache_ttl=300  # Кэширование на 5 минут
)

def get_currency_rates_for_date(date_req):
    """Получает курсы валют на определенную дату через cbrapi"""
    try:
        # Преобразуем дату из формата dd/mm/yyyy в объект datetime
        date_obj = datetime.strptime(date_req, '%d/%m/%Y')

        # Получаем курсы валют через cbrapi
        currencies = cbr_client.get_currencies(on_date=date_obj)

        if not currencies:
            logger.warning(f"Не удалось получить курсы валют на дату {date_req}")
            return None, None

        # Форматируем дату для возврата
        cbr_date = date_obj.strftime('%d.%m.%Y')

        rates = {}
        # Поддерживаемые валюты
        supported_currencies = {
            'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'CHF', 'CAD',
            'AUD', 'TRY', 'KZT', 'AED'
        }

        for currency in currencies:
            currency_code = currency.charcode
            if currency_code in supported_currencies:
                # Нормализуем курс (для JPY и других валют с nominal > 1)
                value = currency.value
                if currency.nominal > 1:
                    value = value / currency.nominal

                rates[currency_code] = {
                    'value': round(value, 4),
                    'name': currency.name,
                    'nominal': currency.nominal,
                    'charcode': currency.charcode,
                    'numcode': currency.numcode
                }

        logger.info(f"Получены курсы {len(rates)} валют на {cbr_date}")
        return rates, cbr_date

    except Exception as e:
        logger.error(f"Ошибка при получении курсов на дату {date_req} через cbrapi: {e}")
        return None, None

def get_currency_rates_with_history():
    """Получает курсы валют на сегодня, вчера и завтра через cbrapi"""
    try:
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # Получаем курсы на сегодня
        rates_today, date_today_str = get_currency_rates_for_date(today.strftime('%d/%m/%Y'))
        if not rates_today:
            logger.error("Не удалось получить курсы на сегодня")
            return {}, 'неизвестная дата', None, None, None, None

        # Получаем курсы на вчера
        rates_yesterday, date_yesterday_str = get_currency_rates_for_date(yesterday.strftime('%d/%m/%Y'))

        # Пытаемся получить курсы на завтра (может не быть доступно)
        rates_tomorrow, date_tomorrow_str = get_currency_rates_for_date(tomorrow.strftime('%d/%m/%Y'))

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
                        'change': round(change, 4),
                        'change_percent': round(change_percent, 2),
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
                        'change': round(change, 4),
                        'change_percent': round(change_percent, 2),
                        'tomorrow_value': tomorrow_value
                    }

        logger.info(f"Успешно получены курсы с историей: сегодня {len(rates_today)}, вчера {len(rates_yesterday) if rates_yesterday else 0}, завтра {len(rates_tomorrow) if rates_tomorrow else 0}")
        return rates_today, date_today_str, rates_yesterday, changes_yesterday, rates_tomorrow, changes_tomorrow

    except Exception as e:
        logger.error(f"Ошибка при получении курсов с историей через cbrapi: {e}")
        return {}, 'неизвестная дата', None, None, None, None

def get_currency_dynamics(currency_code, days=30):
    """Получает динамику курса валюты за указанный период"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        dynamics = cbr_client.get_dynamic(currency_code, start_date, end_date)

        if dynamics:
            # Преобразуем в удобный формат
            dynamic_data = []
            for rate in dynamics:
                dynamic_data.append({
                    'date': rate.date.strftime('%d.%m.%Y'),
                    'value': rate.value,
                    'nominal': rate.nominal
                })

            logger.info(f"Получена динамика для {currency_code} за {days} дней: {len(dynamic_data)} записей")
            return dynamic_data
        else:
            logger.warning(f"Не удалось получить динамику для {currency_code}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении динамики для {currency_code}: {e}")
        return None

def get_metal_rates():
    """Получает курсы драгоценных металлов"""
    try:
        metals = cbr_client.get_metals()

        if metals:
            metal_rates = {}
            for metal in metals:
                metal_rates[metal.code] = {
                    'name': metal.name,
                    'buy': metal.buy,
                    'sell': metal.sell,
                    'date': metal.date.strftime('%d.%m.%Y')
                }

            logger.info(f"Получены курсы {len(metal_rates)} металлов")
            return metal_rates
        else:
            logger.warning("Не удалось получить курсы металлов")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении курсов металлов: {e}")
        return None

def get_key_rate_cbr():
    """Получает ключевую ставку через cbrapi"""
    try:
        # Получаем последние данные по ключевой ставке
        key_rates = cbr_client.get_key_rate()

        if key_rates:
            # Берем последнюю актуальную ставку
            latest_rate = key_rates[-1]

            return {
                'rate': latest_rate.rate,
                'date': latest_rate.date.strftime('%d.%m.%Y'),
                'is_current': True,
                'source': 'cbrapi'
            }
        else:
            logger.warning("Не удалось получить ключевую ставку через cbrapi")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении ключевой ставки через cbrapi: {e}")
        return None

# Функции для обратной совместимости остаются без изменений
def format_currency_rates_message(rates_today: dict, date_today: str,
                                rates_yesterday: dict = None, changes_yesterday: dict = None,
                                rates_tomorrow: dict = None, changes_tomorrow: dict = None) -> str:
    """Форматирует сообщение с курсами валют на сегодня, вчера и завтра"""
    if not rates_today:
        return "❌ Не удалось получить курсы валют от ЦБ РФ."

    message = f"💱 <b>КУРСЫ ВАЛЮТ ЦБ РФ (через cbrapi)</b>\n"
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
    other_currencies = ['AED']  # Сначала AED
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

    message += f"\n\n💡 <i>Официальные курсы ЦБ РФ через cbrapi с историей изменений</i>"
    return message

# Функция для обратной совместимости
def get_currency_rates_with_tomorrow():
    """Совместимая функция для старых вызовов"""
    rates_today, date_today, _, _, rates_tomorrow, changes_tomorrow = get_currency_rates_with_history()

    # Конвертируем changes_tomorrow в старый формат
    changes = {}
    if changes_tomorrow:
        for currency, change_info in changes_tomorrow.items():
            changes[currency] = {
                'change': change_info['change'],
                'change_percent': change_info['change_percent']
            }

    return rates_today, date_today, rates_tomorrow, changes
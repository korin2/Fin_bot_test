"""
Главный файл сервисов - импортирует все API модули для обратной совместимости
"""

# Импортируем все функции из отдельных API модулей
from api_currency import (
    get_currency_rates_for_date,
    get_currency_rates_with_tomorrow,  # для обратной совместимости
    get_currency_rates_with_history,   # новая функция
    format_currency_rates_message
)

from api_keyrate import (
    get_key_rate,
    format_key_rate_message
)

from api_crypto import (
    get_crypto_rates,
    get_crypto_rates_fallback,
    format_crypto_rates_message
)

from api_ai import ask_deepseek

from api_weather import (
    get_weather_moscow,
    format_weather_message
)

from notifications import (
    check_alerts,
    send_daily_rates,
    send_daily_weather
)

from api_ruonia import (
    get_ruonia_rate,
    format_ruonia_message
)

# Экспортируем все функции для обратной совместимости
__all__ = [
    # Currency API
    'get_currency_rates_for_date',
    'get_currency_rates_with_tomorrow',
    'get_currency_rates_with_history',
    'format_currency_rates_message',

    # Key Rate API
    'get_key_rate',
    'format_key_rate_message',

    # ruonia
    'get_ruonia_rate',
    'format_ruonia_message'

    # Crypto API
    'get_crypto_rates',
    'get_crypto_rates_fallback',
    'format_crypto_rates_message',

    # AI API
    'ask_deepseek',

    # Weather API
    'get_weather_moscow',
    'format_weather_message',

    # Notifications
    'check_alerts',
    'send_daily_rates',
    'send_daily_weather'
]

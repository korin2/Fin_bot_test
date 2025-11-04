# services.py - проверяем экспорт
"""
Главный файл сервисов - импортирует все API модули для обратной совместимости
"""

# Импортируем все функции из отдельных API модулей
from api_currency import (
    get_currency_rates_for_date,
    get_currency_rates_with_tomorrow,
    get_currency_rates_with_history,
    format_currency_rates_message
)

from api_keyrate import (
    get_key_rate,
    format_key_rate_message,
    format_combined_rates_message  # Добавляем новую функцию
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

from api_ruonia import (
    get_ruonia_rate,
    format_ruonia_message,
    get_ruonia_historical,           # Новая функция
    format_ruonia_historical_message # Новая функция
)

from notifications import (
    check_alerts,
    send_daily_rates,
    send_daily_weather
)

from config import (
    BOT_VERSION,
    BOT_LAST_UPDATE,
    BOT_CREATION_DATE,
    COINGECKO_API_KEY
)

# Экспортируем все функции для обратной совместимости
__all__ = [
    # Currency API
    'get_currency_rates_for_date',
    'get_currency_rates_with_tomorrow',
    'get_currency_rates_with_history',
    'format_currency_rates_message',

    # Key Rate API
    'get_ruonia_rate',
    'format_ruonia_message',
    'get_ruonia_historical',           # Новая
    'format_ruonia_historical_message' # Новая

    # Crypto API
    'get_crypto_rates',
    'get_crypto_rates_fallback',
    'format_crypto_rates_message',

    # AI API
    'ask_deepseek',

    # Weather API
    'get_weather_moscow',
    'format_weather_message',

    # Ruonia API
    'get_ruonia_rate',
    'format_ruonia_message',

    # Notifications
    'check_alerts',
    'send_daily_rates',
    'send_daily_weather'

    # Bot info
    'BOT_VERSION',
    'BOT_LAST_UPDATE',
    'BOT_CREATION_DATE'

    # API Keys
    'COINGECKO_API_KEY'


]
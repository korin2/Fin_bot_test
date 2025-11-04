# config.py - добавляем API ключ CoinGecko
import os
import logging
import sys

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Токены и API ключи
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Требуется переменная окружения TELEGRAM_BOT_TOKEN")

DEEPSEEK_API_KEY = os.getenv('TG_BOT_APIDEEPSEEK')

# API ключ погоды
WEATHER_API_KEY = os.getenv('API_weather')
if not WEATHER_API_KEY:
    logger.warning("API ключ погоды не найден, будут использоваться демо-данные")

# API ключ CoinGecko
COINGECKO_API_KEY = os.getenv('Fin_bot_coingecko')
if not COINGECKO_API_KEY:
    logger.warning("API ключ CoinGecko не найден, будут использоваться бесплатные запросы")

# ID администраторов
ADMIN_IDS = os.getenv('ADMIN_IDS', '')  # Получаем строку с ID
if ADMIN_IDS:
    try:
        # Преобразуем строку "123,456,789" в список [123, 456, 789]
        ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS.split(',')]
        logger.info(f"Загружены ID администраторов: {ADMIN_IDS}")
    except ValueError as e:
        logger.error(f"Ошибка парсинга ADMIN_IDS: {e}")
        ADMIN_IDS = []
else:
    logger.warning("ADMIN_IDS не настроены, команды администратора будут недоступны")
    ADMIN_IDS = []

# API URLs
CBR_API_BASE = "https://www.cbr.ru/"
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1/"
OPENWEATHER_API_BASE = "http://api.openweathermap.org/data/2.5/"

# Поддерживаемые валюты
SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'CHF', 'CAD', 'AUD', 'TRY', 'KZT', 'AED']

# Настройки погоды
WEATHER_CITY = "Moscow"

# Настройки бота - ВЕРСИЯ И ОБНОВЛЕНИЯ
BOT_VERSION = "1.1.0"
BOT_LAST_UPDATE = "Ноябрь 2025"
BOT_CREATION_DATE = "Октябрь 2025"
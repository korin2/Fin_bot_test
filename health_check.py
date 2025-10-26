
"""
Health check script for monitoring bot status
"""
import requests
import os
import sys
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_bot_health():
    """Проверяет, запущен ли бот и отвечает ли он через Telegram API"""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment")
            return False
        
        # Проверка через Telegram API
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                logger.info(f"✅ Bot is healthy: @{bot_info['username']} ({bot_info['first_name']})")
                return True
            else:
                logger.error(f"❌ Telegram API error: {data.get('description')}")
                return False
        else:
            logger.error(f"❌ HTTP error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ Request timeout - Telegram API not responding")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error - no internet access")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def check_database_connection():
    """Проверяет подключение к базе данных"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.warning("⚠️ DATABASE_URL not configured")
            return True  # Не критично для базовой проверки
        
        import asyncpg
        import asyncio
        
        async def test_connection():
            conn = await asyncpg.connect(database_url)
            # Простой запрос для проверки
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            return result == 1
        
        # Запускаем асинхронную проверку
        result = asyncio.run(test_connection())
        if result:
            logger.info("✅ Database connection is healthy")
            return True
        else:
            logger.error("❌ Database test query failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_apis():
    """Проверяет доступность внешних API"""
    apis_to_check = {
        'ЦБ РФ': 'https://www.cbr.ru/scripts/XML_daily.asp',
        'CoinGecko': 'https://api.coingecko.com/api/v3/ping',
        'OpenWeatherMap': 'https://api.openweathermap.org/data/2.5/weather?q=Moscow&appid=demo'
    }
    
    all_healthy = True
    
    for api_name, api_url in apis_to_check.items():
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code in [200, 401]:  # 401 может быть для API с неверным ключом
                logger.info(f"✅ {api_name} API is accessible")
            else:
                logger.warning(f"⚠️ {api_name} API returned status: {response.status_code}")
                all_healthy = False
        except Exception as e:
            logger.warning(f"⚠️ {api_name} API check failed: {e}")
            all_healthy = False
    
    return all_healthy

def generate_health_report():
    """Генерирует полный отчет о здоровье системы"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'bot_health': check_bot_health(),
        'database_health': check_database_connection(),
        'apis_health': check_apis(),
        'environment': {
            'TELEGRAM_BOT_TOKEN': '✅ Set' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Missing',
            'DATABASE_URL': '✅ Set' if os.getenv('DATABASE_URL') else '❌ Missing',
            'DEEPSEEK_API_KEY': '✅ Set' if os.getenv('TG_BOT_APIDEEPSEEK') else '⚠️ Optional',
            'WEATHER_API_KEY': '✅ Set' if os.getenv('API_weather') else '⚠️ Optional',
            'ADMIN_IDS': '✅ Set' if os.getenv('ADMIN_IDS') else '⚠️ Optional'
        }
    }
    
    # Вывод отчета
    print("\n" + "="*50)
    print("🚀 HEALTH CHECK REPORT")
    print("="*50)
    print(f"📅 Timestamp: {report['timestamp']}")
    print(f"🤖 Bot Health: {'✅ Healthy' if report['bot_health'] else '❌ Unhealthy'}")
    print(f"🗄️ Database: {'✅ Connected' if report['database_health'] else '❌ Failed'}")
    print(f"🌐 External APIs: {'✅ Accessible' if report['apis_health'] else '⚠️ Partial'}")
    print("\n🔧 Environment Variables:")
    for key, value in report['environment'].items():
        print(f"   {key}: {value}")
    print("="*50)
    
    # Возвращаем общий статус
    return all([report['bot_health'], report['database_health']])

if __name__ == '__main__':
    # При запуске скрипта напрямую выполняем проверку
    is_healthy = generate_health_report()
    sys.exit(0 if is_healthy else 1)

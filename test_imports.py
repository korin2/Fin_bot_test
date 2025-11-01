#!/usr/bin/env python3
"""
Скрипт для проверки всех импортов после рефакторинга
"""

def test_imports():
    """Проверяет все основные импорты"""
    try:
        # Проверяем основные модули
        from handlers_basic import start, help_command
        from handlers_finance import show_currency_rates, show_crypto_rates
        from handlers_alerts import show_alerts_menu, alert_command
        from handlers_ai import show_ai_chat
        from handlers_admin import status_command
        from handlers_text import handle_text_messages
        from handlers_callbacks import button_handler
        
        # Проверяем API модули
        from api_currency import get_currency_rates_with_tomorrow
        from api_keyrate import get_key_rate
        from api_crypto import get_crypto_rates
        from api_ai import ask_deepseek
        from api_weather import get_weather_moscow
        from notifications import check_alerts
        
        # Проверяем утилиты
        from utils import create_main_reply_keyboard, split_long_message
        from db import init_db, get_user_alerts
        from config import TOKEN, logger
        from jobs import setup_jobs
        
        print("✅ Все импорты работают корректно!")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Другая ошибка: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Тестирование импортов после рефакторинга...")
    success = test_imports()
    if success:
        print("🎉 Все готово к запуску!")
    else:
        print("⚠️ Есть проблемы с импортами, нужно исправить")

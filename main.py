import logging
import asyncio
import sys
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import Conflict
from config import TOKEN, logger
from db import init_db
from handlers import start, help_command, button_handler, show_currency_rates
from handlers import handle_ai_message, alert_command, myalerts_command, show_key_rate, show_crypto_rates, show_ai_chat
from handlers import show_other_functions, show_bot_stats, show_bot_about, show_settings, show_weather, handle_text_messages
from jobs import setup_jobs

async def post_init(application):
    """Функция инициализации после запуска бота"""
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")

async def shutdown(application):
    """Корректное завершение работы бота"""
    await application.stop()
    await application.shutdown()

def main():
    """Основная функция запуска бота"""
    try:
        application = Application.builder().token(TOKEN).post_init(post_init).build()

        # Регистрация обработчиков команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("rates", show_currency_rates))
        application.add_handler(CommandHandler("currency", show_currency_rates))
        application.add_handler(CommandHandler("keyrate", show_key_rate))
        application.add_handler(CommandHandler("crypto", show_crypto_rates))
        application.add_handler(CommandHandler("ai", show_ai_chat))
        application.add_handler(CommandHandler("alert", alert_command))
        application.add_handler(CommandHandler("myalerts", myalerts_command))
        application.add_handler(CommandHandler("weather", show_weather))
        
        # Обработчики кнопок и сообщений
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Обработчик текстовых сообщений для reply-меню (должен быть после CommandHandler)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

        # Настройка фоновых задач
        setup_jobs(application)

        logger.info("Бот запускается...")
        
        # Запуск с обработкой конфликтов
        application.run_polling(
            close_loop=False,
            stop_signals=None,  # Отключаем обработку сигналов для ручного управления
            drop_pending_updates=True  # Игнорируем старые сообщения при запуске
        )
        
    except Conflict as e:
        logger.error(f"Конфликт: уже запущен другой экземпляр бота. {e}")
        print("❌ ОШИБКА: Бот уже запущен в другом процессе!")
        print("💡 Решение: Найдите и завершите старый процесс:")
        print("   pkill -f 'python.*main.py'")
        print("   или перезагрузите сервер")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

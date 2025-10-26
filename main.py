
import logging
import asyncio
import sys
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TOKEN, logger
from db import init_db
from handlers import (
    start, stop_command, help_command, button_handler, show_currency_rates,
    handle_ai_message, alert_command, myalerts_command, show_key_rate, 
    show_crypto_rates, show_ai_chat, show_other_functions, show_bot_stats, 
    show_bot_about, show_settings, show_weather, handle_text_messages,
    logs_command, clear_logs_command, status_command, myid_command
)
from jobs import setup_jobs

async def post_init(application):
    """Инициализация после запуска бота"""
    await init_db()
    logger.info("База данных инициализирована")
    
    # Логируем информацию о здоровье системы
    try:
        from health_check import check_bot_health, check_database_connection
        bot_health = check_bot_health()
        db_health = check_database_connection()
        logger.info(f"Health check - Bot: {'✅' if bot_health else '❌'}, DB: {'✅' if db_health else '❌'}")
    except Exception as e:
        logger.warning(f"Health check failed: {e}")

def main():
    """Основная функция запуска бота"""
    try:
        # Проверяем обязательные переменные окружения
        if not TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN is required")
            sys.exit(1)
            
        # Создаем приложение
        application = Application.builder().token(TOKEN).post_init(post_init).build()

        # Регистрация обработчиков команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stop", stop_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("rates", show_currency_rates))
        application.add_handler(CommandHandler("currency", show_currency_rates))
        application.add_handler(CommandHandler("keyrate", show_key_rate))
        application.add_handler(CommandHandler("crypto", show_crypto_rates))
        application.add_handler(CommandHandler("ai", show_ai_chat))
        application.add_handler(CommandHandler("alert", alert_command))
        application.add_handler(CommandHandler("myalerts", myalerts_command))
        application.add_handler(CommandHandler("weather", show_weather))
        application.add_handler(CommandHandler("logs", logs_command))
        application.add_handler(CommandHandler("clearlogs", clear_logs_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("myid", myid_command))
   
        # Обработчики кнопок и сообщений
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

        # Настройка фоновых задач
        setup_jobs(application)

        logger.info("Бот запускается...")
        
        # Запуск бота
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

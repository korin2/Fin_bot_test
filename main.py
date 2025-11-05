# main.py
import logging
import asyncio
import sys
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import Conflict
from config import TOKEN, logger
from db import init_db

# Импортируем обработчики из новых модулей
from handlers_basic import (
    start, stop_command, help_command, show_main_menu,
    show_other_functions, show_bot_stats, show_bot_about,
    show_settings, myid_command, show_admin_panel, show_system_stats, show_bot_settings
)
from handlers_finance import (
    show_currency_rates, show_key_rate, show_crypto_rates, show_weather,
    show_ruonia_command, show_ruonia_history
)
from handlers_alerts import (
    alert_command, myalerts_command, show_alerts_menu
)
from handlers_ai import show_ai_chat
from handlers_admin import status_command, logs_command, clear_logs_command, cache_stats_command, refresh_cache_command, clear_cache_command  # 🔄 ДОБАВЛЯЕМ НОВЫЕ КОМАНДЫ
from handlers_text import handle_text_messages
from handlers_callbacks import button_handler
from jobs import setup_jobs

# В main.py обновляем post_init
async def post_init(application):
    """Инициализация после запуска бота"""
    await init_db()
    
    # 🔄 ИНИЦИАЛИЗИРУЕМ КЭШ
    try:
        from cache import init_cache
        init_cache()
        logger.info("✅ База данных и кэш инициализированы")
        
        # 🔄 ПРЕДВАРИТЕЛЬНО ЗАГРУЖАЕМ ДАННЫЕ В КЭШ ПРИ ЗАПУСКЕ
        from handlers_admin import preload_cache_data
        await preload_cache_data()
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации кэша: {e}")
        logger.info("✅ База данных инициализирована (кэш отключен)")

    # Логируем информацию о здоровье системы
    try:
        from health_check import check_bot_health
        bot_health = check_bot_health()
        logger.info(f"Health check - Bot: {'✅' if bot_health else '❌'}")
        logger.info("Database health check skipped during startup")
    except Exception as e:
        logger.warning(f"Health check failed: {e}")

def error_handler(update, context):
    """Обработчик ошибок"""
    try:
        raise context.error
    except Conflict:
        # Игнорируем ошибки конфликта - значит другой экземпляр уже запущен
        logger.warning("Обнаружен конфликт - вероятно запущен другой экземпляр бота")
    except Exception as e:
        logger.error(f"Ошибка в обработчике: {e}")

def main():
    """Основная функция запуска бота"""
    try:
        # Проверяем обязательные переменные окружения
        if not TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN is required")
            sys.exit(1)

        # Создаем приложение
        application = Application.builder().token(TOKEN).post_init(post_init).build()

        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)

        # Регистрация обработчиков команд
        # Основные команды
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stop", stop_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("myid", myid_command))

        # Финансовые команды
        application.add_handler(CommandHandler("rates", show_currency_rates))
        application.add_handler(CommandHandler("currency", show_currency_rates))
        application.add_handler(CommandHandler("keyrate", show_key_rate))
        application.add_handler(CommandHandler("crypto", show_crypto_rates))
        application.add_handler(CommandHandler("weather", show_weather))
        application.add_handler(CommandHandler("ruonia", show_ruonia_command))
        application.add_handler(CommandHandler("ruonia_history", show_ruonia_history))

        # Команды уведомлений
        application.add_handler(CommandHandler("alert", alert_command))
        application.add_handler(CommandHandler("myalerts", myalerts_command))

        # ИИ команды
        application.add_handler(CommandHandler("ai", show_ai_chat))

        # Административные команды
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("logs", logs_command))
        application.add_handler(CommandHandler("clearlogs", clear_logs_command))
        application.add_handler(CommandHandler("cache_stats", cache_stats_command))  # 🔄 НОВАЯ КОМАНДА
        application.add_handler(CommandHandler("refresh_cache", refresh_cache_command))  # 🔄 НОВАЯ КОМАНДА
        application.add_handler(CommandHandler("clear_cache", clear_cache_command))  # 🔄 НОВАЯ КОМАНДА

        # Обработчики кнопок и сообщений
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

        # Настройка фоновых задач
        setup_jobs(application)

        logger.info("Бот запускается...")

        # Запуск бота с обработкой конфликтов
        try:
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query'],
                close_loop=False
            )
        except Conflict:
            logger.warning("Обнаружен конфликт при запуске. Возможно, бот уже запущен.")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

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
from handlers_admin import status_command, logs_command, clear_logs_command
from handlers_text import handle_text_messages
from handlers_callbacks import button_handler
from jobs import setup_jobs

# Добавляем импорт admin_panel
try:
    from admin_panel import show_cache_management, handle_cache_command
    logger.info("✅ Модуль admin_panel успешно импортирован в main.py")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта admin_panel в main.py: {e}")

async def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация базы данных
        logger.info("🔄 Инициализация базы данных...")
        await init_db()
        logger.info("✅ База данных инициализирована")

        # Создание приложения
        logger.info("🔄 Создание приложения бота...")
        application = Application.builder().token(TOKEN).build()
        logger.info("✅ Приложение создано")

        # Добавление обработчиков команд
        logger.info("🔄 Добавление обработчиков команд...")

        # Основные команды
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stop", stop_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("myid", myid_command))

        # Финансовые команды
        application.add_handler(CommandHandler("rates", show_currency_rates))
        application.add_handler(CommandHandler("crypto", show_crypto_rates))
        application.add_handler(CommandHandler("keyrate", show_key_rate))
        application.add_handler(CommandHandler("ruonia", show_ruonia_command))
        application.add_handler(CommandHandler("ruonia_history", show_ruonia_history))
        application.add_handler(CommandHandler("weather", show_weather))

        # Уведомления
        application.add_handler(CommandHandler("alert", alert_command))
        application.add_handler(CommandHandler("myalerts", myalerts_command))

        # ИИ помощник
        application.add_handler(CommandHandler("ai", show_ai_chat))

        # Административные команды
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("logs", logs_command))
        application.add_handler(CommandHandler("clearlogs", clear_logs_command))

        # Обработчики callback-кнопок
        application.add_handler(CallbackQueryHandler(button_handler))

        # Обработчик текстовых сообщений (должен быть последним)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

        logger.info("✅ Обработчики команд добавлены")

        # Настройка фоновых задач
        logger.info("🔄 Настройка фоновых задач...")
        setup_jobs(application)
        logger.info("✅ Фоновые задачи настроены")

        # Запуск бота
        logger.info("🚀 Запуск бота...")

        # Очистка обновлений при запуске (избежание конфликтов)
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Вебхук очищен, pending updates удалены")

        # Запуск polling
        logger.info("🔄 Запуск polling...")
        await application.run_polling(
            allowed_updates=['message', 'callback_query'],
            timeout=60,
            drop_pending_updates=True
        )

    except Conflict as e:
        logger.error(f"❌ Конфликт при запуске бота: {e}")
        logger.info("💡 Возможно, бот уже запущен. Остановите предыдущий процесс.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )

    # Запуск асинхронного приложения
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка: {e}")
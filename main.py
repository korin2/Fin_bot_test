import logging
import asyncio
import sys
import os
import signal
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import Conflict, RetryAfter
from config import TOKEN, logger
from db import init_db
from handlers import start, help_command, button_handler, show_currency_rates
from handlers import handle_ai_message, alert_command, myalerts_command, show_key_rate, show_crypto_rates, show_ai_chat
from handlers import show_other_functions, show_bot_stats, show_bot_about, show_settings, show_weather, handle_text_messages
from jobs import setup_jobs
from railway_config import setup_railway_webhook

# Глобальная переменная для отслеживания состояния
bot_running = False

async def post_init(application):
    """Функция инициализации после запуска бота"""
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")

async def shutdown(application):
    """Корректное завершение работы бота"""
    global bot_running
    bot_running = False
    logger.info("Завершение работы бота...")
    await application.stop()
    await application.shutdown()
    logger.info("Бот остановлен")

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"Получен сигнал {signum}, завершаем работу...")
    sys.exit(0)

async def run_polling_safe(application):
    """Безопасный запуск polling с обработкой конфликтов"""
    global bot_running
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries and not bot_running:
        try:
            logger.info(f"Попытка запуска polling (попытка {retry_count + 1}/{max_retries})")
            
            # Останавливаем любые предыдущие обновления
            await application.bot.delete_webhook(drop_pending_updates=True)
            
            # Запускаем polling
            bot_running = True
            await application.start()
            await application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )
            
            logger.info("Bot polling started successfully")
            return True
            
        except Conflict as e:
            retry_count += 1
            logger.error(f"Конфликт при запуске (попытка {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                wait_time = retry_count * 5
                logger.info(f"Ждем {wait_time} секунд перед повторной попыткой...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Достигнуто максимальное количество попыток. Завершаем работу.")
                return False
                
        except RetryAfter as e:
            logger.warning(f"Rate limit, waiting {e.retry_after} seconds: {e}")
            await asyncio.sleep(e.retry_after)
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запуске polling: {e}")
            return False
    
    return False

def main():
    """Основная функция запуска бота"""
    global bot_running
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Создаем приложение
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
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

        # Настройка фоновых задач
        try:
            setup_jobs(application)
        except Exception as e:
            logger.warning(f"JobQueue не настроен: {e}")

        logger.info("Запуск бота...")
        
        # Пытаемся использовать Webhook на Railway
        if os.getenv('RAILWAY_ENVIRONMENT'):
            logger.info("Обнаружена среда Railway, пробуем Webhook...")
            if setup_railway_webhook(application, TOKEN):
                logger.info("Webhook успешно настроен")
                return
        
        # Если Webhook не сработал, используем polling
        logger.info("Используем polling...")
        
        # Запускаем event loop
        loop = asyncio.get_event_loop()
        
        # Запускаем polling
        success = loop.run_until_complete(run_polling_safe(application))
        
        if success:
            logger.info("Бот успешно запущен и работает")
            
            # Бесконечный цикл работы
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                logger.info("Получен сигнал KeyboardInterrupt")
            finally:
                loop.run_until_complete(shutdown(application))
        else:
            logger.error("Не удалось запустить бота после нескольких попыток")
            sys.exit(1)
        
    except Conflict as e:
        logger.error(f"Критический конфликт: {e}")
        print("❌ ОШИБКА: Бот уже запущен в другом процессе!")
        print("💡 Решение на Railway:")
        print("   1. Перейдите в панель Railway")
        print("   2. Нажмите 'Restart' для вашего сервиса")
        print("   3. Убедитесь, что запущен только один экземпляр")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

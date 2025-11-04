# main.py (упрощенный до максимума)
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Конфигурация
TOKEN = "2020352781:AAEMRFfklLNDqO22fxWMpP6ofmP8WXJSaSc"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Простой обработчик start"""
    await update.message.reply_text("Бот запущен!")

async def help_command(update, context):
    """Простой обработчик help"""
    await update.message.reply_text("Помощь: используйте /start")

async def handle_text(update, context):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    await update.message.reply_text(f"Вы сказали: {text}")

async def main():
    """Основная функция"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем базовые обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запускаем бота
    logger.info("🚀 Запуск бота...")
    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
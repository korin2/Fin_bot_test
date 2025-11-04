# main.py (using Updater - старый стиль)
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Конфигурация
TOKEN = "2020352781:AAEMRFfklLNDqO22fxWMpP6ofmP8WXJSaSc"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text("Бот запущен!")

def help_command(update, context):
    update.message.reply_text("Помощь: используйте /start")

def main():
    """Основная функция"""
    try:
        # Создаем Updater (старый стиль, но более стабильный)
        updater = Updater(TOKEN, use_context=True)

        # Получаем dispatcher
        dp = updater.dispatcher

        # Добавляем обработчики
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, start))

        # Запускаем polling
        logger.info("🚀 Запуск бота (Updater)...")
        updater.start_polling(drop_pending_updates=True)

        # Бот работает до принудительной остановки
        updater.idle()

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    main()
import logging
import psutil
import platform
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import logger, ADMIN_IDS, BOT_VERSION, BOT_LAST_UPDATE
from utils import log_user_action, create_main_reply_keyboard

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статус бота и системную информацию"""
    try:
        # Проверяем права администратора
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ Эта команда только для администраторов")
            return

        log_user_action(update.effective_user.id, "view_status")

        # Системная информация
        system_info = f"🖥️ <b>Системная информация</b>\n"
        system_info += f"• OS: {platform.system()} {platform.release()}\n"
        system_info += f"• Python: {platform.python_version()}\n"
        system_info += f"• CPU: {psutil.cpu_percent()}%\n"
        system_info += f"• Memory: {psutil.virtual_memory().percent}%\n"
        system_info += f"• Disk: {psutil.disk_usage('/').percent}%\n\n"

        # Информация о боте
        from db import get_all_users, get_all_alerts
        users = await get_all_users()
        alerts = await get_all_alerts()

        bot_info = f"🤖 <b>Информация о боте</b>\n"
        bot_info += f"• Версия: {BOT_VERSION}\n"  # Используем из config
        bot_info += f"• Последнее обновление: {BOT_LAST_UPDATE}\n"  # Используем из config
        bot_info += f"• Запущен: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        bot_info += f"• Пользователей: {len(users)}\n"
        bot_info += f"• Уведомлений: {len(alerts)}\n"
        bot_info += f"• Администраторов: {len(ADMIN_IDS)}\n\n"

        # Статус сервисов
        services_info = f"🔧 <b>Статус сервисов</b>\n"

        # Проверка ЦБ РФ
        try:
            from services import get_currency_rates_for_date
            rates, _ = get_currency_rates_for_date(datetime.now().strftime('%d/%m/%Y'))
            services_info += "• ЦБ РФ: ✅ Работает\n"
        except:
            services_info += "• ЦБ РФ: ❌ Ошибка\n"

        # Проверка CoinGecko
        try:
            from services import get_crypto_rates
            crypto_data = get_crypto_rates()
            services_info += "• CoinGecko: ✅ Работает\n" if crypto_data else "• CoinGecko: ❌ Ошибка\n"
        except:
            services_info += "• CoinGecko: ❌ Ошибка\n"

        # Проверка DeepSeek
        from config import DEEPSEEK_API_KEY
        services_info += f"• DeepSeek AI: {'✅ Доступен' if DEEPSEEK_API_KEY else '❌ Не настроен'}\n"

        # Проверка погоды
        from config import WEATHER_API_KEY
        services_info += f"• Погода: {'✅ Настроена' if WEATHER_API_KEY and WEATHER_API_KEY != 'demo_key_12345' else '⚠️ Демо-данные'}\n"

        full_message = system_info + bot_info + services_info
        full_message += f"\n💡 <i>Бот работает стабильно</i>"

        await update.message.reply_text(full_message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка в команде status: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении статуса системы",
            reply_markup=create_main_reply_keyboard()
        )

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает последние логи (только для администраторов)"""
    try:
        if not ADMIN_IDS:
            await update.message.reply_text("❌ Администраторы не настроены")
            return

        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ Эта команда только для администраторов")
            return

        log_user_action(update.effective_user.id, "view_logs")

        # Чтение последних логов
        try:
            with open('bot.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-20:]  # Последние 20 строк
                log_text = ''.join(last_lines)
        except FileNotFoundError:
            log_text = "Файл логов не найден"

        if len(log_text) > 4000:
            log_text = log_text[-4000:]  # Обрезаем если слишком длинный

        await update.message.reply_text(
            f"📋 <b>Последние логи:</b>\n<code>{log_text}</code>",
            parse_mode='HTML',
            reply_markup=create_main_reply_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка в команде logs: {e}")
        await update.message.reply_text(
            "❌ Ошибка при чтении логов",
            reply_markup=create_main_reply_keyboard()
        )

async def clear_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Очищает логи (только для администраторов)"""
    try:
        if not ADMIN_IDS:
            await update.message.reply_text("❌ Администраторы не настроены")
            return

        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ Эта команда только для администраторов")
            return

        log_user_action(update.effective_user.id, "clear_logs")

        # Очистка файла логов
        open('bot.log', 'w').close()

        await update.message.reply_text(
            "✅ Логи успешно очищены",
            reply_markup=create_main_reply_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка в команде clear_logs: {e}")
        await update.message.reply_text(
            "❌ Ошибка при очистке логов",
            reply_markup=create_main_reply_keyboard()
        )

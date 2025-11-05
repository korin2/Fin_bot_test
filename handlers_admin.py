import logging
import psutil
import platform
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup  # 🔄 ДОБАВЛЯЕМ ИМПОРТ
from telegram.ext import ContextTypes
from config import logger, ADMIN_IDS, BOT_VERSION, BOT_LAST_UPDATE
from utils import log_user_action, create_main_reply_keyboard, create_admin_functions_keyboard
from db import update_user_info

# 🔄 ДОБАВЛЯЕМ ИМПОРТ ДЛЯ КЭШИРОВАНИЯ
from cache import get_cache_stats, force_refresh_cache, clear_cache

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
            from api_currency import get_currency_rates_for_date
            rates, _ = get_currency_rates_for_date(datetime.now().strftime('%d/%m/%Y'))
            services_info += "• ЦБ РФ: ✅ Работает\n"
        except:
            services_info += "• ЦБ РФ: ❌ Ошибка\n"

        # Проверка CoinGecko
        try:
            from api_crypto import get_crypto_rates
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

async def cache_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статистику кэша"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        log_user_action(update.effective_user.id, "view_cache_stats")
        
        stats = get_cache_stats()
        
        message = "💾 <b>СТАТИСТИКА КЭША</b>\n\n"
        message += f"📊 <b>Всего записей:</b> {stats['total_entries']}\n\n"
        
        if stats['entries']:
            message += "📋 <b>Записи кэша:</b>\n"
            for key, info in stats['entries'].items():
                status = "🟢" if not info['is_expired'] else "🔴"
                message += (
                    f"{status} <b>{key}:</b>\n"
                    f"   ⏱️ Возраст: {info['age_human']}\n"
                    f"   🕒 TTL осталось: {info['remaining_ttl']} сек.\n"
                    f"   📏 Размер: {info['data_size']} символов\n\n"
                )
        else:
            message += "📭 <i>Кэш пуст</i>\n\n"
            
        message += "💡 <b>График обновления:</b>\n"
        message += "• 💱 Курсы валют: каждый час\n"
        message += "• 💎 Ключевая ставка: раз в 24 часа\n" 
        message += "• 📊 RUONIA: раз в 24 часа\n"
        message += "• ₿ Криптовалюты: каждые 30 минут\n"
        message += "• 🌤️ Погода: каждые 30 минут\n\n"
        
        message += "🔄 <i>Используйте кнопки ниже для управления кэшем</i>"

        # 🔄 ИСПОЛЬЗУЕМ KeyboardButton И ReplyKeyboardMarkup
        keyboard = [
            [KeyboardButton("🔄 Обновить кэш")],
            [KeyboardButton("🧹 Очистить кэш")],
            [KeyboardButton("📊 Обновить статистику")],
            [KeyboardButton("🔙 Назад к админ-панели")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Ошибка при показе статистики кэша: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке статистики кэша.")

async def refresh_cache_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Принудительно обновляет кэш"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        log_user_action(update.effective_user.id, "refresh_cache")
        
        success = force_refresh_cache()
        
        if success:
            message = (
                "🔄 <b>КЭШ ОБНОВЛЕН</b>\n\n"
                "✅ Все данные кэша принудительно обновлены.\n\n"
                "💡 <i>Следующие запросы получат свежие данные от API</i>"
            )
        else:
            message = "❌ <b>Ошибка при обновлении кэша</b>"
            
        await update.message.reply_text(message, parse_mode='HTML')
        
        # Показываем обновленную статистику
        await cache_stats_command(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша: {e}")
        await update.message.reply_text("❌ Ошибка при обновлении кэша.")

async def clear_cache_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Очищает кэш"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        log_user_action(update.effective_user.id, "clear_cache")
        
        success = clear_cache()
        
        if success:
            message = (
                "🧹 <b>КЭШ ОЧИЩЕН</b>\n\n"
                "✅ Все данные кэша удалены.\n\n"
                "💡 <i>Следующие запросы загрузят свежие данные от API</i>"
            )
        else:
            message = "❌ <b>Ошибка при очистке кэша</b>"
            
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {e}")
        await update.message.reply_text("❌ Ошибка при очистке кэша.")

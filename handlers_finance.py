# handlers_finance.py - убедимся, что все функции есть
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from utils import log_user_action, create_main_reply_keyboard
from api_currency import get_currency_rates_with_history, format_currency_rates_message
from api_keyrate import get_key_rate, format_key_rate_message, format_combined_rates_message
from api_crypto import get_crypto_rates, get_crypto_rates_fallback, format_crypto_rates_message
from api_weather import get_weather_moscow, format_weather_message
from api_ruonia import get_ruonia_rate, format_ruonia_message, get_ruonia_historical, format_ruonia_historical_message

async def show_currency_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает курсы валют"""
    try:
        log_user_action(update.effective_user.id, "view_currency_rates")

        # Используем новую функцию с историей
        rates_today, date_today, rates_yesterday, changes_yesterday, rates_tomorrow, changes_tomorrow = get_currency_rates_with_history()

        if not rates_today:
            await update.message.reply_text(
                "❌ Не удалось получить курсы валют.",
                reply_markup=create_main_reply_keyboard()
            )
            return

        message = format_currency_rates_message(
            rates_today, date_today, rates_yesterday, changes_yesterday,
            rates_tomorrow, changes_tomorrow
        )
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе курсов валют: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.", reply_markup=create_main_reply_keyboard())

async def show_key_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает ключевую ставку и RUONIA"""
    try:
        log_user_action(update.effective_user.id, "view_key_rate")

        # Показываем сообщение о загрузке
        loading_message = "🔄 <b>Загружаем данные о ставках...</b>"
        await update.message.reply_text(loading_message, parse_mode='HTML')

        # Получаем обе ставки
        key_rate_data = get_key_rate()
        ruonia_data = get_ruonia_rate()

        if not key_rate_data:
            await update.message.reply_text(
                "❌ Не удалось получить данные по ключевой ставке от ЦБ РФ.",
                reply_markup=create_main_reply_keyboard()
            )
            return

        # Используем комбинированное сообщение
        message = format_combined_rates_message(key_rate_data, ruonia_data)
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе ключевой ставки: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.", reply_markup=create_main_reply_keyboard())

# handlers_finance.py - упрощаем обработку crypto
async def show_crypto_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает курсы криптовалют"""
    try:
        log_user_action(update.effective_user.id, "view_crypto_rates")

        # Показываем сообщение о загрузке
        loading_message = "🔄 <b>Загружаем курсы криптовалют...</b>"
        await update.message.reply_text(loading_message, parse_mode='HTML')

        # Получаем данные
        crypto_rates = get_crypto_rates()

        if not crypto_rates:
            error_msg = "❌ <b>Не удалось получить курсы криптовалют.</b>"
            await update.message.reply_text(error_msg, parse_mode='HTML', reply_markup=create_main_reply_keyboard())
            return

        message_text = format_crypto_rates_message(crypto_rates)

        await update.message.reply_text(message_text, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе курсов криптовалют: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.", reply_markup=create_main_reply_keyboard())

async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает текущую погоду в Москве"""
    try:
        log_user_action(update.effective_user.id, "view_weather")

        # Показываем сообщение о загрузке
        loading_message = "🔄 <b>Загружаем данные о погоде...</b>"
        await update.message.reply_text(loading_message, parse_mode='HTML')

        # Получаем данные о погоде
        weather_data = get_weather_moscow()
        message = format_weather_message(weather_data)

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе погоды: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении данных о погоде.",
            reply_markup=create_main_reply_keyboard()
        )

async def show_ruonia_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает только ставку RUONIA"""
    try:
        log_user_action(update.effective_user.id, "view_ruonia")

        # Показываем сообщение о загрузке
        loading_message = "🔄 <b>Загружаем данные о ставке RUONIA...</b>"
        await update.message.reply_text(loading_message, parse_mode='HTML')

        ruonia_data = get_ruonia_rate()

        if not ruonia_data:
            await update.message.reply_text(
                "❌ Не удалось получить данные по ставке RUONIA от ЦБ РФ.",
                reply_markup=create_main_reply_keyboard()
            )
            return

        message = format_ruonia_message(ruonia_data)
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе ставки RUONIA: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.", reply_markup=create_main_reply_keyboard())

async def show_ruonia_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает историю ставки RUONIA"""
    try:
        log_user_action(update.effective_user.id, "view_ruonia_history")

        # Показываем сообщение о загрузке
        loading_message = "🔄 <b>Загружаем исторические данные RUONIA...</b>"
        await update.message.reply_text(loading_message, parse_mode='HTML')

        # Получаем исторические данные (последние 30 дней)
        historical_data = get_ruonia_historical(days=30)

        if not historical_data:
            await update.message.reply_text(
                "❌ Не удалось получить исторические данные по ставке RUONIA.",
                reply_markup=create_main_reply_keyboard()
            )
            return

        message = format_ruonia_historical_message(historical_data)
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе истории RUONIA: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.", reply_markup=create_main_reply_keyboard())
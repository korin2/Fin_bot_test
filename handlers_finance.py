import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from utils import log_user_action, create_main_reply_keyboard
# Обновляем импорты
from api_currency import get_currency_rates_with_history, format_currency_rates_message
from api_keyrate import get_key_rate, format_key_rate_message
from api_crypto import get_crypto_rates, get_crypto_rates_fallback, format_crypto_rates_message
from api_weather import get_weather_moscow, format_weather_message
from api_ruonia import get_ruonia_rate, format_ruonia_message


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

# видимо лишнеее уже
async def show_key_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает ключевую ставку"""
    try:
        log_user_action(update.effective_user.id, "view_key_rate")

        key_rate_data = get_key_rate()

        if not key_rate_data:
            await update.message.reply_text(
                "❌ Не удалось получить ключевую ставку.",
                reply_markup=create_main_reply_keyboard()
            )
            return

        message = format_key_rate_message(key_rate_data)
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе ключевой ставки: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.", reply_markup=create_main_reply_keyboard())
# видимо лишнеее уже

async def show_cbr_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает ключевую ставку и RUONIA"""
    try:
        log_user_action(update.effective_user.id, "view_cbr_rates")

        # Получаем обе ставки
        key_rate_data = get_key_rate()
        ruonia_data = get_ruonia_rate()

        if not key_rate_data and not ruonia_data:
            await update.message.reply_text(
                "❌ Не удалось получить данные по ставкам ЦБ РФ.",
                reply_markup=create_main_reply_keyboard()
            )
            return

        # Формируем объединенное сообщение
        message = "🏛️ <b>СТАВКИ ЦБ РФ</b>\n\n"

        if key_rate_data:
            message += (
                f"💎 <b>Ключевая ставка:</b> {key_rate_data['rate']:.2f}%\n"
                f"📅 <b>Дата установления:</b> {key_rate_data.get('date', 'неизвестно')}\n\n"
            )

        if ruonia_data:
            message += (
                f"📊 <b>Ставка RUONIA:</b> {ruonia_data['rate']:.2f}%\n"
                f"📅 <b>Дата:</b> {ruonia_data.get('date', 'неизвестно')}\n\n"
            )

        # Добавляем пояснения
        message += (
            "💡 <b>Пояснения:</b>\n"
            "• <b>Ключевая ставка</b> - основная процентная ставка ЦБ РФ\n"
            "• <b>RUONIA</b> - средняя ставка по однодневным рублевым депозитам\n\n"
        )

        # Информация об источниках
        sources = []
        if key_rate_data and key_rate_data.get('source') == 'demo':
            sources.append("ключевой ставки")
        if ruonia_data and ruonia_data.get('source') == 'demo':
            sources.append("RUONIA")

        if sources:
            message += f"⚠️ <i>Используются демо-данные для: {', '.join(sources)}</i>"
        else:
            message += "✅ <i>Данные получены с официального сайта ЦБ РФ</i>"

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе ставок ЦБ РФ: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных.", reply_markup=create_main_reply_keyboard())





async def show_crypto_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает курсы криптовалют"""
    try:
        log_user_action(update.effective_user.id, "view_crypto_rates")

        # Показываем сообщение о загрузке
        loading_message = "🔄 <b>Загружаем курсы криптовалют...</b>"
        await update.message.reply_text(loading_message, parse_mode='HTML')

        # Получаем данные
        crypto_rates = get_crypto_rates()

        # Если не удалось получить данные, используем fallback
        if not crypto_rates:
            logger.warning("Не удалось получить данные от CoinGecko, используем fallback")
            crypto_rates = get_crypto_rates_fallback()

        if not crypto_rates:
            error_msg = "❌ <b>Не удалось получить курсы криптовалют.</b>"
            await update.message.reply_text(error_msg, parse_mode='HTML', reply_markup=create_main_reply_keyboard())
            return

        message_text = format_crypto_rates_message(crypto_rates)

        # Добавляем предупреждение если используем демо-данные
        if crypto_rates.get('source') == 'demo_fallback':
            message_text += "\n\n⚠️ <i>Используются демонстрационные данные (CoinGecko API недоступен)</i>"

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

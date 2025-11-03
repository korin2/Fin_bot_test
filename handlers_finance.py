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

# Остальные функции остаются без изменений...
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

# В handlers_finance.py добавляем новые функции

async def show_metal_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает курсы драгоценных металлов"""
    try:
        log_user_action(update.effective_user.id, "view_metal_rates")

        # Показываем сообщение о загрузке
        loading_message = "🔄 <b>Загружаем курсы драгоценных металлов...</b>"
        await update.message.reply_text(loading_message, parse_mode='HTML')

        # Получаем данные о металлах
        from api_currency import get_metal_rates
        metal_rates = get_metal_rates()

        if not metal_rates:
            await update.message.reply_text(
                "❌ Не удалось получить курсы драгоценных металлов.",
                reply_markup=create_main_reply_keyboard()
            )
            return

        # Форматируем сообщение
        message = "🥇 <b>КУРСЫ ДРАГОЦЕННЫХ МЕТАЛЛОВ ЦБ РФ</b>\n\n"

        for metal_code, metal_data in metal_rates.items():
            message += (
                f"💎 <b>{metal_data['name']}</b>\n"
                f"   💰 <b>Покупка:</b> {metal_data['buy']:.2f} руб/г\n"
                f"   💵 <b>Продажа:</b> {metal_data['sell']:.2f} руб/г\n"
                f"   📅 <b>Дата:</b> {metal_data['date']}\n\n"
            )

        message += "💡 <i>Курсы установлены ЦБ РФ для операций с драгоценными металлами</i>"

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе курсов металлов: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении данных о металлах.",
            reply_markup=create_main_reply_keyboard()
        )

async def show_currency_dynamics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает динамику курса валюты за период"""
    try:
        log_user_action(update.effective_user.id, "view_currency_dynamics")

        args = context.args
        if not args or len(args) < 1:
            await update.message.reply_text(
                "📈 <b>Использование:</b> /dynamics &lt;валюта&gt; [дней]\n\n"
                "💡 <b>Примеры:</b>\n"
                "• <code>/dynamics USD</code> - динамика USD за 30 дней\n"
                "• <code>/dynamics EUR 7</code> - динамика EUR за 7 дней\n"
                "• <code>/dynamics JPY 14</code> - динамика JPY за 14 дней\n\n"
                "💱 <b>Доступные валюты:</b> USD, EUR, GBP, JPY, CNY, CHF, CAD, AUD, TRY, KZT, AED",
                parse_mode='HTML',
                reply_markup=create_main_reply_keyboard()
            )
            return

        currency = args[0].upper()
        days = 30
        if len(args) > 1:
            try:
                days = int(args[1])
                if days < 1 or days > 365:
                    days = 30
            except ValueError:
                days = 30

        # Показываем сообщение о загрузке
        loading_message = f"🔄 <b>Загружаем динамику {currency} за {days} дней...</b>"
        await update.message.reply_text(loading_message, parse_mode='HTML')

        # Получаем динамику
        from api_currency import get_currency_dynamics
        dynamics = get_currency_dynamics(currency, days)

        if not dynamics:
            await update.message.reply_text(
                f"❌ Не удалось получить динамику для {currency}.",
                reply_markup=create_main_reply_keyboard()
            )
            return

        # Форматируем сообщение
        message = f"📈 <b>ДИНАМИКА {currency} ЗА {days} ДНЕЙ</b>\n\n"

        # Показываем первые и последние 5 записей
        if len(dynamics) > 10:
            message += "<b>Начало периода:</b>\n"
            for i, day in enumerate(dynamics[:5]):
                message += f"   {day['date']}: {day['value']:.4f} руб.\n"

            message += "\n<b>Конец периода:</b>\n"
            for i, day in enumerate(dynamics[-5:]):
                message += f"   {day['date']}: {day['value']:.4f} руб.\n"
        else:
            for day in dynamics:
                message += f"   {day['date']}: {day['value']:.4f} руб.\n"

        # Рассчитываем общее изменение
        if len(dynamics) >= 2:
            first = dynamics[0]['value']
            last = dynamics[-1]['value']
            change = last - first
            change_percent = (change / first) * 100 if first > 0 else 0

            message += f"\n📊 <b>Общее изменение:</b> {change:+.4f} руб. ({change_percent:+.2f}%)"

        message += f"\n\n💡 <i>Динамика курса {currency} по данным ЦБ РФ</i>"

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_main_reply_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе динамики валюты: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении динамики.",
            reply_markup=create_main_reply_keyboard()
        )

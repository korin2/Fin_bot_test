# handlers_text.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from utils import log_user_action, create_main_reply_keyboard, create_alerts_keyboard
from handlers_basic import show_main_menu, show_other_functions, help_command, show_bot_stats, show_settings, show_bot_about
from handlers_finance import show_currency_rates, show_crypto_rates, show_key_rate, show_weather
from handlers_ai import show_ai_chat, handle_ai_message, show_ai_examples
from db import clear_user_alerts

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений для reply-меню"""
    try:
        user_message = update.message.text
        user_id = update.effective_user.id

        # Логируем текстовое сообщение
        log_user_action(user_id, "text_message", {"message": user_message})

        logger.info(f"Получено сообщение: '{user_message}' от пользователя {user_id}")

        # Обработка меню уведомлений
        if user_message == "🔔 Уведомления":
            logger.info(f"Пользователь {user_id} нажал кнопку Уведомления")
            from handlers_alerts import show_alerts_menu
            await show_alerts_menu(update, context)
            return

        elif user_message == "💱 Создать уведомление":
            logger.info(f"Пользователь {user_id} нажал кнопку Создать уведомление")
            from handlers_alerts import start_create_alert
            await start_create_alert(update, context)
            return

        elif user_message == "📋 Мои уведомления":
            logger.info(f"Пользователь {user_id} нажал кнопку Мои уведомления")
            from handlers_alerts import myalerts_command
            await myalerts_command(update, context)
            return

        elif user_message == "🌤️ Погода (вкл/выкл)":
            logger.info(f"Пользователь {user_id} нажал кнопку Погода (вкл/выкл)")
            from handlers_alerts import toggle_weather_notifications
            await toggle_weather_notifications(update, context)
            return

        elif user_message == "🗑 Очистить все уведомления":
            logger.info(f"Пользователь {user_id} нажал кнопку Очистить все уведомления")
            user_id = update.effective_user.id
            await clear_user_alerts(user_id)
            await update.message.reply_text(
                "✅ Все уведомления очищены",
                reply_markup=create_alerts_keyboard()
            )
            return

        elif user_message == "🔙 Главное меню":
            logger.info(f"Пользователь {user_id} нажал кнопку Главное меню")
            clear_user_context(context)
            await show_main_menu(update, context)
            return

        # Обработка процесса создания уведомления
        if context.user_data.get('creating_alert'):
            alert_stage = context.user_data.get('alert_stage')
            logger.info(f"Пользователь {user_id} в процессе создания уведомления, этап: {alert_stage}")

            if alert_stage == 'select_currency':
                from handlers_alerts import handle_currency_selection
                await handle_currency_selection(update, context)
                return

            elif alert_stage == 'select_direction':
                from handlers_alerts import handle_direction_selection
                await handle_direction_selection(update, context)
                return

            elif alert_stage == 'enter_threshold':
                from handlers_alerts import handle_threshold_input
                await handle_threshold_input(update, context)
                return

        # Обработка навигации назад
        if user_message == "🔙 Назад к уведомлениям":
            logger.info(f"Пользователь {user_id} нажал Назад к уведомлениям")
            from handlers_alerts import show_alerts_menu
            await show_alerts_menu(update, context)
            return

        elif user_message == "🔙 Назад к валютам":
            logger.info(f"Пользователь {user_id} нажал Назад к валютам")
            context.user_data['alert_stage'] = 'select_currency'
            from handlers_alerts import start_create_alert
            await start_create_alert(update, context)
            return

        elif user_message == "🔙 Назад к условиям":
            logger.info(f"Пользователь {user_id} нажал Назад к условиям")
            currency = context.user_data.get('alert_currency')
            if currency:
                context.user_data['alert_stage'] = 'select_direction'
                from handlers_alerts import handle_currency_selection
                await handle_currency_selection(update, context)
            else:
                from handlers_alerts import start_create_alert
                await start_create_alert(update, context)
            return

        # Обработка других функций
        if user_message == "💱 Курсы валют":
            await show_currency_rates(update, context)
        elif user_message == "₿ Криптовалюты":
            await show_crypto_rates(update, context)
        elif user_message == "💎 Ключевая ставка ЦБ РФ":
            await show_key_rate(update, context)
        elif user_message == "🤖 ИИ помощник":
            await show_ai_chat(update, context)
        elif user_message == "🌤️ Погода":
            await show_weather(update, context)
        elif user_message == "🔧 Другие функции":
            await show_other_functions(update, context)
        elif user_message == "❓ Помощь":
            await help_command(update, context)
        elif user_message == "📊 Статистика":
            await show_bot_stats(update, context)
        elif user_message == "⚙️ Настройки":
            await show_settings(update, context)
        elif user_message == "ℹ️ О боте":
            await show_bot_about(update, context)
        elif user_message == "💡 Примеры вопросов":
            await show_ai_examples(update, context)
        elif user_message == "🔄 Новый вопрос":
            await show_ai_chat(update, context)

        # Если сообщение не распознано как команда меню, пробуем обработать как запрос к ИИ
        elif context.user_data.get('ai_mode') == True:
            await handle_ai_message(update, context)
        else:
            # Если не режим ИИ и не команда меню, показываем подсказку
            await update.message.reply_text(
                "🤔 <b>Не понял вашу команду</b>\n\n"
                "Используйте кнопки меню ниже или команды:\n"
                "/start - Главное меню\n"
                "/help - Справка по командам",
                parse_mode='HTML',
                reply_markup=create_main_reply_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка в обработчике текстовых сообщений: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке сообщения.",
            reply_markup=create_main_reply_keyboard()
        )

def clear_user_context(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Очищает контекст пользователя для быстрого возврата в меню"""
    keys_to_clear = [
        'ai_mode', 'creating_alert', 'alert_stage',
        'alert_currency', 'alert_direction', 'alert_direction_display',
        'waiting_for_ai', 'last_ai_response'
    ]
    for key in keys_to_clear:
        context.user_data.pop(key, None)
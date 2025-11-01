import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from handlers_basic import help_command, show_main_menu, show_bot_stats, show_bot_about, show_settings
from handlers_finance import show_currency_rates, show_crypto_rates, show_key_rate, show_weather
from handlers_alerts import myalerts_command, show_alerts_menu
from handlers_ai import show_ai_chat
from db import clear_user_alerts

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на inline-кнопки"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'help':
            await help_command(update, context)
        elif data == 'back_to_main':
            context.user_data['ai_mode'] = False
            await show_main_menu(update, context)
        elif data == 'currency_rates':
            await show_currency_rates(update, context)
        elif data == 'crypto_rates':
            await show_crypto_rates(update, context)
        elif data == 'key_rate':
            await show_key_rate(update, context)
        elif data == 'ai_chat':
            await show_ai_chat(update, context)
        elif data == 'my_alerts':
            await myalerts_command(update, context)
        elif data == 'other_functions':
            from handlers_basic import show_other_functions
            await show_other_functions(update, context)
        elif data == 'weather':
            await show_weather(update, context)
        elif data == 'stats':
            await show_bot_stats(update, context)
        elif data == 'about':
            await show_bot_about(update, context)
        elif data == 'settings':
            await show_settings(update, context)
        elif data == 'clear_all_alerts':
            user_id = update.effective_user.id
            await clear_user_alerts(user_id)
            await query.edit_message_text(
                "✅ Все уведомления очищены",
                reply_markup=create_main_reply_keyboard()
            )
        elif data == 'create_alert':
            await query.edit_message_text(
                "📝 <b>Создание уведомления</b>\n\n"
                "Используйте команду:\n"
                "<code>/alert USD RUB 80 above</code>\n\n"
                "💡 <b>Примеры:</b>\n"
                "• <code>/alert USD RUB 85 above</code> - уведомит когда USD выше 85 руб.\n"
                "• <code>/alert EUR RUB 90 below</code> - уведомит когда EUR ниже 90 руб.",
                parse_mode='HTML',
                reply_markup=create_main_reply_keyboard()
            )
        else:
            await query.edit_message_text(
                "🔄 <b>Функция в разработке</b>",
                parse_mode='HTML',
                reply_markup=create_main_reply_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")

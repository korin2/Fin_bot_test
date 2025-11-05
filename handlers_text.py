# handlers_text.py
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import logger, ADMIN_IDS
from utils import log_user_action, create_main_reply_keyboard, create_alerts_keyboard
from db import clear_user_alerts

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений для reply-меню"""
    try:
        user_message = update.message.text
        user_id = update.effective_user.id

        # Логируем текстовое сообщение
        log_user_action(user_id, "text_message", {"message": user_message})

        logger.info(f"Получено сообщение: '{user_message}' от пользователя {user_id}")

        # Обработка административных функций
        if user_message == "👑 Админ-панель" and user_id in ADMIN_IDS:
            from handlers_basic import show_admin_panel
            await show_admin_panel(update, context)
            return

        elif user_message == "📊 Статистика системы" and user_id in ADMIN_IDS:
            from handlers_basic import show_system_stats
            await show_system_stats(update, context)
            return

        elif user_message == "🔧 Настройки бота" and user_id in ADMIN_IDS:
            from handlers_basic import show_bot_settings
            await show_bot_settings(update, context)
            return

        elif user_message == "📋 Логи бота" and user_id in ADMIN_IDS:
            from handlers_admin import logs_command
            await logs_command(update, context)
            return

        # 🔄 ДОБАВЛЯЕМ ОБРАБОТКУ НОВОЙ КНОПКИ
        elif user_message == "⏰ Расписание кэша" and user_id in ADMIN_IDS:
            from handlers_admin import cache_schedule_command
            await cache_schedule_command(update, context)
            return

        elif user_message == "🔙 Назад к функциям":
            from handlers_basic import show_other_functions
            await show_other_functions(update, context)
            return

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
            from handlers_finance import show_currency_rates
            await show_currency_rates(update, context)
        elif user_message == "₿ Криптовалюты":
            from handlers_finance import show_crypto_rates
            await show_crypto_rates(update, context)
        elif user_message == "🏛️ Ставки ЦБ РФ":
            from handlers_finance import show_key_rate
            await show_key_rate(update, context)
        elif user_message == "📊 RUONIA":
            from handlers_finance import show_ruonia_command
            await show_ruonia_command(update, context)
        elif user_message == "🤖 ИИ помощник":
            from handlers_ai import show_ai_chat
            await show_ai_chat(update, context)
        elif user_message == "🌤️ Погода":
            from handlers_finance import show_weather
            await show_weather(update, context)
        elif user_message == "🔧 Другие функции":
            try:
                from handlers_basic import show_other_functions
                await show_other_functions(update, context)
            except Exception as e:
                logger.error(f"Ошибка при импорте show_other_functions: {e}")
                await update.message.reply_text(
                    "❌ Временная ошибка при загрузке функций.",
                    reply_markup=create_main_reply_keyboard()
                )
        elif user_message == "❓ Помощь":
            from handlers_basic import help_command
            await help_command(update, context)
        elif user_message == "⚙️ Настройки":
            from handlers_basic import show_settings
            await show_settings(update, context)
        elif user_message == "ℹ️ О боте":
            from handlers_basic import show_bot_about
            await show_bot_about(update, context)
        elif user_message == "💡 Примеры вопросов":
            from handlers_ai import show_ai_examples
            await show_ai_examples(update, context)
        elif user_message == "🔄 Новый вопрос":
            from handlers_ai import show_ai_chat
            await show_ai_chat(update, context)

        # Обработка управления кэшем
        elif user_message == "💾 Статистика кэша" and user_id in ADMIN_IDS:
            from handlers_admin import cache_stats_command
            await cache_stats_command(update, context)
            return

        elif user_message == "🔄 Обновить кэш" and user_id in ADMIN_IDS:
            from handlers_admin import refresh_cache_command
            await refresh_cache_command(update, context)
            return

        elif user_message == "🧹 Очистить кэш" and user_id in ADMIN_IDS:
            from handlers_admin import clear_cache_command
            await clear_cache_command(update, context)
            return

        elif user_message == "📊 Обновить статистику" and user_id in ADMIN_IDS:
            from handlers_admin import cache_stats_command
            await cache_stats_command(update, context)
            return

        # 🔄 ОБРАБОТКА УПРАВЛЕНИЯ РАСПИСАНИЕМ
        elif user_message == "⏰ Расписание кэша" and user_id in ADMIN_IDS:
            from handlers_admin import cache_schedule_command
            await cache_schedule_command(update, context)
            return

        # В handlers_text.py обновляем подсказки для кнопок
        elif user_message == "💱 Изменить курс валют" and user_id in ADMIN_IDS:
            await update.message.reply_text(
                "📝 <b>Изменение расписания курсов валют</b>\n\n"
                "💡 <b>Пример команды:</b>\n"
                "<code>/set_schedule currency_rates 07:00,10:00,13:00,16:00,19:00</code>\n\n"
                "🕒 <b>Можно указать любое количество времен через запятую</b>\n"
                "📊 <b>Текущее расписание:</b> 07:00,10:00,13:00,16:00,19:00 МСК",
                parse_mode='HTML'
            )
            return

        elif user_message == "📊 Изменить ключевую ставку" and user_id in ADMIN_IDS:
            await update.message.reply_text(
                "📝 <b>Изменение расписания ключевой ставки</b>\n\n"
                "💡 <b>Пример команды:</b>\n"
                "<code>/set_schedule key_rate 08:00</code>\n"
                "<code>/set_schedule key_rate 08:00,12:00,16:00</code>\n\n"
                "🕒 <b>Можно указать любое количество времен через запятую</b>\n"
                "📊 <b>Текущее расписание:</b> 08:00 МСК",
                parse_mode='HTML'
            )
            return

        elif user_message == "📊 Изменить RUONIA" and user_id in ADMIN_IDS:
            await update.message.reply_text(
                "📝 <b>Изменение расписания RUONIA</b>\n\n"
                "💡 <b>Пример команды:</b>\n"
                "<code>/set_schedule ruonia_rate 08:00</code>\n"
                "<code>/set_schedule ruonia_rate 08:00,12:00,16:00,20:00</code>\n\n"
                "🕒 <b>Можно указать любое количество времен через запятую</b>\n"
                "📊 <b>Текущее расписание:</b> 08:00 МСК",
                parse_mode='HTML'
            )
            return

        elif user_message == "₿ Изменить крипту" and user_id in ADMIN_IDS:
            await update.message.reply_text(
                "📝 <b>Изменение расписания криптовалют</b>\n\n"
                "💡 <b>Пример команды:</b>\n"
                "<code>/set_schedule crypto_rates 09:00,12:00,15:00,18:00,21:00</code>\n\n"
                "🕒 <b>Можно указать любое количество времен через запятую</b>\n"
                "📊 <b>Текущее расписание:</b> 09:00,12:00,15:00,18:00,21:00 МСК",
                parse_mode='HTML'
            )
            return

        elif user_message == "🌤️ Изменить погоду" and user_id in ADMIN_IDS:
            await update.message.reply_text(
                "📝 <b>Изменение расписания погоды</b>\n\n"
                "💡 <b>Пример команды:</b>\n"
                "<code>/set_schedule weather 06:00,12:00,18:00</code>\n"
                "<code>/set_schedule weather 06:00,09:00,12:00,15:00,18:00,21:00</code>\n\n"
                "🕒 <b>Можно указать любое количество времен через запятую</b>\n"
                "📊 <b>Текущее расписание:</b> 06:00,12:00,18:00 МСК",
                parse_mode='HTML'
            )
            return

        # Если сообщение не распознано как команда меню, пробуем обработать как запрос к ИИ
        elif context.user_data.get('ai_mode') == True:
            from handlers_ai import handle_ai_message
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

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Быстрое отображение главного меню без лишних операций"""
    try:
        user = update.effective_user
        greeting = f"Привет, {user.first_name}!" if user.first_name else "Привет!"

        menu_message = (
            f'{greeting}\n'
            f'👇 <b>Выберите действие в меню ниже:</b>'
        )

        reply_markup = create_main_reply_keyboard()
        await update.message.reply_text(menu_message, parse_mode='HTML', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Ошибка при показе главного меню: {e}")
        await update.message.reply_text("❌ Произошла ошибка.", reply_markup=create_main_reply_keyboard())

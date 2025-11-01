import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import logger, SUPPORTED_CURRENCIES
from utils import log_user_action, create_alerts_keyboard, create_currency_selection_keyboard, create_alert_direction_keyboard
from db import get_user_alerts, clear_user_alerts, add_alert
from services import get_currency_rates_with_tomorrow

async def show_alerts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню уведомлений"""
    try:
        user_id = update.effective_user.id
        log_user_action(user_id, "view_alerts_menu")
        
        message = (
            "🔔 <b>УПРАВЛЕНИЕ УВЕДОМЛЕНИЯМИ</b>\n\n"
            "Здесь вы можете создавать и управлять уведомлениями о курсах валют.\n\n"
            "💡 <b>Как это работает:</b>\n"
            "• Бот проверяет курсы каждые 30 минут\n"
            "• При срабатывании условия вы получаете уведомление\n"
            "• Уведомление автоматически удаляется после срабатывания\n\n"
            "👇 <b>Выберите действие:</b>"
        )
        
        reply_markup = create_alerts_keyboard()
        logger.info(f"Отправка меню уведомлений пользователю {user_id}")
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Ошибка при показе меню уведомлений: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке меню уведомлений.", reply_markup=create_main_reply_keyboard())

async def start_create_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс создания уведомления - выбор валюты"""
    try:
        user_id = update.effective_user.id
        log_user_action(user_id, "start_create_alert")
        
        # Сохраняем состояние создания уведомления
        context.user_data['creating_alert'] = True
        context.user_data['alert_stage'] = 'select_currency'
        
        message = (
            "💱 <b>СОЗДАНИЕ УВЕДОМЛЕНИЯ</b>\n\n"
            "📝 <b>Шаг 1 из 3:</b> Выберите валюту\n\n"
            "👇 <b>Выберите валюту из списка:</b>"
        )
        
        reply_markup = create_currency_selection_keyboard()
        logger.info(f"Начало создания уведомления для пользователя {user_id}")
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Ошибка при начале создания уведомления: {e}")
        await update.message.reply_text("❌ Ошибка при создании уведомления.", reply_markup=create_alerts_keyboard())

async def handle_currency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор валюты для уведомления"""
    try:
        selected_currency = update.message.text
        
        if selected_currency not in SUPPORTED_CURRENCIES:
            await update.message.reply_text(
                "❌ Пожалуйста, выберите валюту из списка ниже:",
                reply_markup=create_currency_selection_keyboard()
            )
            return
        
        # Сохраняем выбранную валюту
        context.user_data['alert_currency'] = selected_currency
        context.user_data['alert_stage'] = 'select_direction'
        
        # Получаем текущий курс для информации
        rates_today, _, _, _ = get_currency_rates_with_tomorrow()
        current_rate = "N/A"
        if rates_today and selected_currency in rates_today:
            current_rate = f"{rates_today[selected_currency]['value']:.2f}"
        
        message = (
            f"💱 <b>СОЗДАНИЕ УВЕДОМЛЕНИЯ</b>\n\n"
            f"📝 <b>Шаг 2 из 3:</b> Выберите условие\n\n"
            f"💹 <b>Выбранная валюта:</b> {selected_currency}\n"
            f"💰 <b>Текущий курс:</b> {current_rate} руб.\n\n"
            f"👇 <b>Выберите условие уведомления:</b>\n"
            f"• <b>Выше порога</b> - уведомит когда курс ПРЕВЫСИТ указанное значение\n"
            f"• <b>Ниже порога</b> - уведомит когда курс СТАНЕТ НИЖЕ указанного значения"
        )
        
        reply_markup = create_alert_direction_keyboard()
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Ошибка при выборе валюты: {e}")
        await update.message.reply_text("❌ Ошибка при выборе валюты.", reply_markup=create_alerts_keyboard())

async def handle_direction_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор направления уведомления"""
    try:
        direction_text = update.message.text
        
        if direction_text == "📈 Выше порога":
            direction = 'above'
            direction_display = 'выше'
        elif direction_text == "📉 Ниже порога":
            direction = 'below'
            direction_display = 'ниже'
        else:
            await update.message.reply_text(
                "❌ Пожалуйста, выберите условие из списка:",
                reply_markup=create_alert_direction_keyboard()
            )
            return
        
        # Сохраняем направление
        context.user_data['alert_direction'] = direction
        context.user_data['alert_direction_display'] = direction_display
        context.user_data['alert_stage'] = 'enter_threshold'
        
        currency = context.user_data['alert_currency']
        
        message = (
            f"💱 <b>СОЗДАНИЕ УВЕДОМЛЕНИЯ</b>\n\n"
            f"📝 <b>Шаг 3 из 3:</b> Укажите пороговое значение\n\n"
            f"💹 <b>Валюта:</b> {currency}\n"
            f"📊 <b>Условие:</b> курс станет <b>{direction_display}</b> указанного значения\n\n"
            f"💰 <b>Введите пороговое значение в рублях:</b>\n\n"
            f"💡 <i>Пример: 85.50 или 90</i>"
        )
        
        keyboard = [[KeyboardButton("🔙 Назад к условиям")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Ошибка при выборе направления: {e}")
        await update.message.reply_text("❌ Ошибка при выборе условия.", reply_markup=create_alerts_keyboard())

async def handle_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ввод порогового значения и создает уведомление"""
    try:
        threshold_text = update.message.text
        
        # Проверяем, не является ли сообщение командой назад
        if threshold_text == "🔙 Назад к условиям":
            context.user_data['alert_stage'] = 'select_direction'
            await handle_currency_selection(update, context)
            return
        
        # Парсим пороговое значение
        try:
            threshold = float(threshold_text.replace(',', '.'))
            if threshold <= 0:
                raise ValueError("Порог должен быть положительным числом")
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Неверный формат числа!</b>\n\n"
                "💰 <b>Введите пороговое значение в рублях:</b>\n"
                "💡 <i>Пример: 85.50 или 90</i>",
                parse_mode='HTML'
            )
            return
        
        # Получаем данные из context
        currency = context.user_data.get('alert_currency')
        direction = context.user_data.get('alert_direction')
        direction_display = context.user_data.get('alert_direction_display')
        
        if not all([currency, direction]):
            await update.message.reply_text(
                "❌ Произошла ошибка при создании уведомления. Начните заново.",
                reply_markup=create_alerts_keyboard()
            )
            return
        
        user_id = update.effective_user.id
        
        # Добавляем уведомление в базу данных
        await add_alert(user_id, currency, 'RUB', threshold, direction)
        
        # Получаем текущий курс для информации
        rates_today, _, _, _ = get_currency_rates_with_tomorrow()
        current_rate = "N/A"
        if rates_today and currency in rates_today:
            current_rate = f"{rates_today[currency]['value']:.2f}"
        
        # Формируем сообщение об успехе
        success_message = (
            f"✅ <b>УВЕДОМЛЕНИЕ СОЗДАНО!</b>\n\n"
            f"💱 <b>Пара:</b> {currency}/RUB\n"
            f"🎯 <b>Порог:</b> {threshold} руб.\n"
            f"📊 <b>Условие:</b> курс <b>{direction_display}</b> {threshold} руб.\n"
            f"💹 <b>Текущий курс:</b> {current_rate} руб.\n\n"
            f"⏰ <i>Уведомление будет проверяться каждые 30 минут</i>\n"
            f"🔔 <i>При срабатывании вы получите сообщение</i>\n"
            f"📋 <i>Все уведомления можно посмотреть в 'Мои уведомления'</i>"
        )
        
        # Очищаем данные создания уведомления
        context.user_data.pop('creating_alert', None)
        context.user_data.pop('alert_stage', None)
        context.user_data.pop('alert_currency', None)
        context.user_data.pop('alert_direction', None)
        context.user_data.pop('alert_direction_display', None)
        
        await update.message.reply_text(
            success_message,
            parse_mode='HTML',
            reply_markup=create_alerts_keyboard()
        )
        
        # Логируем создание уведомления
        log_user_action(user_id, "alert_created", {
            "currency": currency,
            "threshold": threshold,
            "direction": direction
        })
            
    except Exception as e:
        logger.error(f"Ошибка при создании уведомления: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при создании уведомления.",
            reply_markup=create_alerts_keyboard()
        )

async def myalerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает активные уведомления пользователя"""
    try:
        user_id = update.effective_user.id
        log_user_action(user_id, "view_my_alerts")
        
        alerts = await get_user_alerts(user_id)
        
        if not alerts:
            message = (
                "📭 <b>У вас нет активных уведомлений.</b>\n\n"
                "💡 Нажмите <b>💱 Создать уведомление</b> чтобы добавить первое уведомление!"
            )
            
            await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_alerts_keyboard())
            return
        
        message = "🔔 <b>ВАШИ АКТИВНЫЕ УВЕДОМЛЕНИЯ</b>\n\n"
        
        for i, alert in enumerate(alerts, 1):
            from_curr = alert['from_currency']
            to_curr = alert['to_currency']
            threshold = alert['threshold']
            direction = alert['direction']
            
            # Получаем текущий курс для сравнения
            rates_today, _, _, _ = get_currency_rates_with_tomorrow()
            current_rate = "N/A"
            if rates_today and from_curr in rates_today:
                current_rate = f"{rates_today[from_curr]['value']:.2f}"
            
            direction_display = 'выше' if direction == 'above' else 'ниже'
            status_icon = "🟢" if alert.get('is_active', True) else "🔴"
            
            message += (
                f"{status_icon} <b>{i}. {from_curr} → {to_curr}</b>\n"
                f"   🎯 Порог: <b>{threshold} руб.</b>\n"
                f"   📊 Условие: курс <b>{direction_display}</b> {threshold} руб.\n"
                f"   💱 Текущий курс: <b>{current_rate} руб.</b>\n\n"
            )
        
        message += (
            "⏰ <i>Уведомления проверяются каждые 30 минут автоматически</i>\n"
            "💡 <i>При срабатывании уведомление автоматически удаляется</i>"
        )
        
        reply_markup = create_alerts_keyboard()
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в команде /myalerts: {e}")
        error_message = "❌ <b>Ошибка при получении уведомлений.</b>"
        await update.message.reply_text(error_message, parse_mode='HTML', reply_markup=create_alerts_keyboard())

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создание уведомления о курсе валюты через команду"""
    try:
        log_user_action(update.effective_user.id, "create_alert", {"args": context.args})
        
        args = context.args
        
        if len(args) != 4:
            await update.message.reply_text(
                "📝 <b>Использование:</b> /alert &lt;из&gt; &lt;в&gt; &lt;порог&gt; &lt;above|below&gt;\n\n"
                "💡 <b>Примеры:</b>\n"
                "• <code>/alert USD RUB 80 above</code> - уведомить когда USD выше 80 руб.\n"
                "• <code>/alert EUR RUB 90 below</code> - уведомить когда EUR ниже 90 руб.\n"
                "• <code>/alert AED RUB 22 above</code> - уведомить когда AED выше 22 руб.",
                parse_mode='HTML',
                reply_markup=create_main_reply_keyboard()
            )
            return
        
        from_curr, to_curr = args[0].upper(), args[1].upper()
        
        # Проверяем поддерживаемые валюты
        supported_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'CHF', 'CAD', 'AUD', 'TRY', 'KZT', 'AED']
        if from_curr not in supported_currencies:
            await update.message.reply_text(
                f"❌ Валюта <b>{from_curr}</b> не поддерживается.\n\n"
                f"💱 <b>Доступные валюты:</b> {', '.join(supported_currencies)}",
                parse_mode='HTML',
                reply_markup=create_main_reply_keyboard()
            )
            return
        
        # Проверяем, что целевая валюта - RUB
        if to_curr != 'RUB':
            await update.message.reply_text(
                "❌ В настоящее время поддерживаются только уведомления для пар с RUB.\n"
                "💡 Используйте: <code>/alert USD RUB 80 above</code>",
                parse_mode='HTML',
                reply_markup=create_main_reply_keyboard()
            )
            return
        
        try:
            threshold = float(args[2])
            if threshold <= 0:
                raise ValueError("Порог должен быть положительным числом")
        except ValueError:
            await update.message.reply_text(
                "❌ Порог должен быть положительным числом.",
                reply_markup=create_main_reply_keyboard()
            )
            return
        
        direction = args[3].lower()
        if direction not in ['above', 'below']:
            await update.message.reply_text(
                "❌ Направление должно быть 'above' или 'below'.",
                reply_markup=create_main_reply_keyboard()
            )
            return
        
        user_id = update.effective_message.from_user.id
        
        # Добавляем уведомление
        await add_alert(user_id, from_curr, to_curr, threshold, direction)
        
        # Получаем текущий курс для информации
        rates_today, _, _, _ = get_currency_rates_with_tomorrow()
        current_rate = "N/A"
        if rates_today and from_curr in rates_today:
            current_rate = f"{rates_today[from_curr]['value']:.2f}"
        
        success_message = (
            f"✅ <b>УВЕДОМЛЕНИЕ УСТАНОВЛЕНО!</b>\n\n"
            f"💱 <b>Пара:</b> {from_curr}/{to_curr}\n"
            f"🎯 <b>Порог:</b> {threshold} руб.\n"
            f"📊 <b>Условие:</b> курс <b>{'выше' if direction == 'above' else 'ниже'}</b> {threshold} руб.\n"
            f"💹 <b>Текущий курс:</b> {current_rate} руб.\n\n"
            f"💡 Уведомление будет проверяться каждые 30 минут\n"
            f"🔔 При срабатывании вы получите сообщение"
        )
        
        await update.message.reply_text(
            success_message,
            parse_mode='HTML',
            reply_markup=create_main_reply_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в команде /alert: {e}")
        await update.message.reply_text(
            f"❌ Произошла ошибка при установке уведомления:\n<code>{str(e)}</code>",
            parse_mode='HTML',
            reply_markup=create_main_reply_keyboard()
        )

async def handle_alerts_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает навигацию назад в процессе создания уведомления"""
    try:
        back_text = update.message.text
        
        if back_text == "🔙 Назад к уведомлениям":
            await show_alerts_menu(update, context)
        elif back_text == "🔙 Назад к валютам":
            context.user_data['alert_stage'] = 'select_currency'
            await start_create_alert(update, context)
        elif back_text == "🔙 Назад к условиям":
            currency = context.user_data.get('alert_currency')
            if currency:
                context.user_data['alert_stage'] = 'select_direction'
                await handle_currency_selection(update, context)
            else:
                await start_create_alert(update, context)
                
    except Exception as e:
        logger.error(f"Ошибка при навигации назад: {e}")
        await update.message.reply_text("❌ Ошибка навигации.", reply_markup=create_alerts_keyboard())

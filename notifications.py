import logging
from telegram.ext import ContextTypes
from config import logger
from db import get_all_active_alerts, deactivate_alert, get_all_users
from api_currency import get_currency_rates_with_tomorrow
from api_keyrate import get_key_rate
from api_weather import get_weather_moscow, format_weather_message

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет активные уведомления и отправляет уведомления при срабатывании"""
    try:
        alerts = await get_all_active_alerts()
        if not alerts:
            return
        
        rates_today, _, _, _ = get_currency_rates_with_tomorrow()
        if not rates_today:
            return
        
        for alert in alerts:
            user_id = alert['user_id']
            from_curr = alert['from_currency']
            threshold = alert['threshold']
            direction = alert['direction']
            alert_id = alert['id']
            
            if from_curr in rates_today:
                current_rate = rates_today[from_curr]['value']
                triggered = False
                
                if direction == 'above' and current_rate >= threshold:
                    triggered = True
                elif direction == 'below' and current_rate <= threshold:
                    triggered = True
                
                if triggered:
                    message = (
                        f"🔔 <b>УВЕДОМЛЕНИЕ СРАБОТАЛО!</b>\n\n"
                        f"💱 <b>Пара:</b> {from_curr}/RUB\n"
                        f"🎯 <b>Порог:</b> {threshold} руб.\n"
                        f"💹 <b>Текущий курс:</b> {current_rate:.2f} руб.\n"
                        f"📊 <b>Условие:</b> курс <b>{'выше' if direction == 'above' else 'ниже'}</b> {threshold} руб.\n\n"
                        f"✅ <i>Уведомление выполнено и удалено.</i>"
                    )
                    
                    await context.bot.send_message(
                        chat_id=user_id, 
                        text=message, 
                        parse_mode='HTML'
                    )
                    await deactivate_alert(alert_id)
                    
    except Exception as e:
        logger.error(f"Ошибка при проверке уведомлений: {e}")

async def send_daily_rates(context: ContextTypes.DEFAULT_TYPE):
    """Ежедневная рассылка основных финансовых данных"""
    try:
        logger.info("🔄 [РАССЫЛКА КУРСОВ] Функция запущена")
        
        users = await get_all_users()
        logger.info(f"📊 [РАССЫЛКА КУРСОВ] Получено пользователей: {len(users)}")
        
        if not users:
            logger.warning("⚠️ [РАССЫЛКА КУРСОВ] Нет пользователей для рассылки")
            return
        
        # Формируем сводное сообщение
        logger.info("💱 [РАССЫЛКА КУРСОВ] Получаем данные о курсах валют...")
        rates_today, date_today, _, _ = get_currency_rates_with_tomorrow()
        
        logger.info("💎 [РАССЫЛКА КУРСОВ] Получаем ключевую ставку...")
        key_rate_data = get_key_rate()
        
        message = "🌅 <b>ЕЖЕДНЕВНАЯ ФИНАНСОВАЯ СВОДКА</b>\n\n"
        
        # Добавляем курсы валют
        if rates_today:
            message += "💱 <b>Основные курсы ЦБ РФ:</b>\n"
            for currency in ['USD', 'EUR']:
                if currency in rates_today:
                    rate = rates_today[currency]['value']
                    message += f"   {currency}: <b>{rate:.2f} руб.</b>\n"
            message += "\n"
        
        # Добавляем ключевую ставку
        if key_rate_data:
            message += f"💎 <b>Ключевая ставка:</b> {key_rate_data['rate']:.2f}%\n\n"
        
        message += "💡 Используйте команды бота для подробной информации"
        
        logger.info(f"📝 [РАССЫЛКА КУРСОВ] Сообщение сформировано: {len(message)} символов")
        logger.info("📨 [РАССЫЛКА КУРСОВ] Начинаем отправку сообщений...")
        
        # Отправляем всем пользователям
        success_count = 0
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=message,
                    parse_mode='HTML'
                )
                success_count += 1
                logger.info(f"✅ [РАССЫЛКА КУРСОВ] Отправлено пользователю {user['user_id']}")
            except Exception as e:
                logger.error(f"❌ [РАССЫЛКА КУРСОВ] Ошибка отправки пользователю {user['user_id']}: {e}")
        
        logger.info(f"🎉 [РАССЫЛКА КУРСОВ] Рассылка завершена. Успешно: {success_count}/{len(users)}")
                
    except Exception as e:
        logger.error(f"💥 [РАССЫЛКА КУРСОВ] Критическая ошибка: {e}")

async def send_daily_weather(context: ContextTypes.DEFAULT_TYPE):
    """Ежедневная рассылка погоды"""
    try:
        logger.info("🔄 [РАССЫЛКА ПОГОДЫ] Функция запущена")
        
        users = await get_all_users()
        logger.info(f"📊 [РАССЫЛКА ПОГОДЫ] Получено пользователей: {len(users)}")
        
        if not users:
            logger.warning("⚠️ [РАССЫЛКА ПОГОДЫ] Нет пользователей для рассылки")
            return
        
        # Получаем погоду
        logger.info("🌤️ [РАССЫЛКА ПОГОДЫ] Получаем данные о погоде...")
        weather_data = get_weather_moscow()
        message = format_weather_message(weather_data)
        
        # Добавляем заголовок для рассылки
        full_message = f"🌅 <b>ЕЖЕДНЕВНАЯ РАССЫЛКА ПОГОДЫ</b>\n\n{message}"
        
        logger.info("📨 [РАССЫЛКА ПОГОДЫ] Начинаем отправку сообщений...")
        
        # Отправляем всем пользователям
        success_count = 0
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=full_message,
                    parse_mode='HTML'
                )
                success_count += 1
                logger.info(f"✅ [РАССЫЛКА ПОГОДЫ] Отправлено пользователю {user['user_id']}")
            except Exception as e:
                logger.error(f"❌ [РАССЫЛКА ПОГОДЫ] Ошибка отправки пользователю {user['user_id']}: {e}")
        
        logger.info(f"🎉 [РАССЫЛКА ПОГОДЫ] Рассылка завершена. Успешно: {success_count}/{len(users)}")
                
    except Exception as e:
        logger.error(f"💥 [РАССЫЛКА ПОГОДЫ] Критическая ошибка: {e}")

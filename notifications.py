# notifications.py - добавляем импорт RUONIA
import logging
from telegram.ext import ContextTypes
from config import logger
from db import get_all_active_alerts, deactivate_alert, get_all_users, get_users_with_weather_notifications
from api_currency import get_currency_rates_with_tomorrow, get_currency_rates_with_history
from api_keyrate import get_key_rate
from api_weather import get_weather_moscow, format_weather_message
from api_ruonia import get_ruonia_rate  # Добавляем импорт RUONIA

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
        rates_today, date_today, _, _, rates_tomorrow, changes_tomorrow = get_currency_rates_with_history()

        logger.info("💎 [РАССЫЛКА КУРСОВ] Получаем ключевую ставку...")
        key_rate_data = get_key_rate()

        logger.info("📊 [РАССЫЛКА КУРСОВ] Получаем ставку RUONIA...")
        ruonia_data = get_ruonia_rate()  # Теперь функция доступна

        message = "🌅 <b>ЕЖЕДНЕВНАЯ ФИНАНСОВАЯ СВОДКА</b>\n\n"

        # Добавляем курсы валют с завтрашними изменениями
        if rates_today:
            message += "💱 <b>Основные курсы ЦБ РФ:</b>\n"

            for currency in ['USD', 'EUR']:
                if currency in rates_today:
                    today_rate = rates_today[currency]['value']

                    # Формируем строку с завтрашними изменениями если есть
                    if changes_tomorrow and currency in changes_tomorrow:
                        change_info = changes_tomorrow[currency]
                        change_icon = "📈" if change_info['change'] > 0 else "📉" if change_info['change'] < 0 else "➡️"

                        message += (
                            f"  \n <b>{currency}:</b> {today_rate:.2f} руб.\n"
                            f"      <i>Завтра: {change_info['tomorrow_value']:.2f} руб. {change_icon}</i>\n"
                            f"      <i>Изменение: {change_info['change']:+.2f} руб. ({change_info['change_percent']:+.2f}%)</i>\n"
                        )
                    elif rates_tomorrow and currency in rates_tomorrow:
                        # Если курс на завтра есть, но изменений нет
                        tomorrow_rate = rates_tomorrow[currency]['value']
                        message += (
                            f" \n  <b>{currency}:</b> {today_rate:.2f} руб.\n"
                            f"      <i>Завтра: {tomorrow_rate:.2f} руб. ➡️</i>\n"
                        )
                    else:
                        # Если курса на завтра нет
                        message += (
                            f"   <b>{currency}:</b> {today_rate:.2f} руб.\n"
                            f"      <i>Завтра: ЦБ РФ еще не установил курс</i>\n"
                        )

            message += "\n"

        # Добавляем ключевую ставку
        if key_rate_data:
            message += f"🏛️ <b>Ключевая ставка:</b> {key_rate_data['rate']:.2f}%\n"

        # Добавляем ставку RUONIA
        if ruonia_data:
            message += f"\n📊 <b>Ставка RUONIA:</b> {ruonia_data['rate']:.2f}%\n"

            # Если есть обе ставки, показываем сравнение
            if key_rate_data and ruonia_data:
                key_rate = key_rate_data['rate']
                ruonia_rate = ruonia_data['rate']
                difference = key_rate - ruonia_rate

                if difference > 0:
                    comparison = f"📈 Ключевая ставка выше на {difference:.2f}%"
                elif difference < 0:
                    comparison = f"📉 Ключевая ставка ниже на {abs(difference):.2f}%"
                else:
                    comparison = "➡️ Ставки равны"

                message += f"   <i>{comparison}</i>\n"

        message += "\n💡 Используйте команды бота для подробной информации"
        message += "\n🏛️ Подробнее о ставках: /keyrate"
        message += "\n📊 История RUONIA: /ruonia_history"

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
    """Ежедневная рассылка погоды только пользователям с включенными уведомлениями"""
    try:
        logger.info("🔄 [РАССЫЛКА ПОГОДЫ] Функция запущена")

        # Получаем только пользователей с включенными уведомлениями о погоде
        user_ids = await get_users_with_weather_notifications()
        logger.info(f"📊 [РАССЫЛКА ПОГОДЫ] Пользователей с уведомлениями: {len(user_ids)}")

        if not user_ids:
            logger.warning("⚠️ [РАССЫЛКА ПОГОДЫ] Нет пользователей с включенными уведомлениями")
            return

        # Получаем погоду
        logger.info("🌤️ [РАССЫЛКА ПОГОДЫ] Получаем данные о погоде...")
        weather_data = get_weather_moscow()
        message = format_weather_message(weather_data)

        # Добавляем заголовок для рассылки
        full_message = f"🌅 <b>ЕЖЕДНЕВНАЯ РАССЫЛКА ПОГОДЫ</b>\n\n{message}"

        logger.info("📨 [РАССЫЛКА ПОГОДЫ] Начинаем отправку сообщений...")

        # Отправляем только пользователям с включенными уведомлениями
        success_count = 0
        for user_id in user_ids:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=full_message,
                    parse_mode='HTML'
                )
                success_count += 1
                logger.info(f"✅ [РАССЫЛКА ПОГОДЫ] Отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(f"❌ [РАССЫЛКА ПОГОДЫ] Ошибка отправки пользователю {user_id}: {e}")

        logger.info(f"🎉 [РАССЫЛКА ПОГОДЫ] Рассылка завершена. Успешно: {success_count}/{len(user_ids)}")

    except Exception as e:
        logger.error(f"💥 [РАССЫЛКА ПОГОДЫ] Критическая ошибка: {e}")
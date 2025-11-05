import logging
import psutil
import platform
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import logger, ADMIN_IDS, BOT_VERSION, BOT_LAST_UPDATE
from utils import log_user_action, create_main_reply_keyboard, create_admin_functions_keyboard
from db import update_user_info, get_user_actions_stats, get_user_detailed_stats, get_user_info

# 🔄 ДОБАВЛЯЕМ ИМПОРТ ДЛЯ КЭШИРОВАНИЯ
from cache import get_cache_stats, force_refresh_cache, clear_cache

# 🔄 ДОБАВЛЯЕМ ФУНКЦИЮ ДЛЯ КЛАВИАТУРЫ СТАТИСТИКИ
def create_user_stats_keyboard():
    """Создает клавиатуру для управления статистикой пользователей"""
    keyboard = [
        [KeyboardButton("📈 Общая статистика")],
        [KeyboardButton("👤 Детали по пользователю")],
        [KeyboardButton("🔄 Обновить статистику")],
        [KeyboardButton("🔙 Назад к админ-панели")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


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

        # 🔄 ОЧИЩАЕМ КЭШ
        success = force_refresh_cache()

        if success:
            message = (
                "🔄 <b>КЭШ ОБНОВЛЕН</b>\n\n"
                "✅ Все данные кэша принудительно обновлены.\n\n"
                "⏳ <i>Загружаем свежие данные от API...</i>"
            )

            await update.message.reply_text(message, parse_mode='HTML')

            # 🔄 ЗАПОЛНЯЕМ КЭШ СВЕЖИМИ ДАННЫМИ
            await preload_cache_data()

            message = (
                "✅ <b>КЭШ ЗАПОЛНЕН</b>\n\n"
                "💾 Все основные данные загружены в кэш:\n"
                "• 💱 Курсы валют ЦБ РФ\n"
                "• 💎 Ключевая ставка\n"
                "• 📊 RUONIA\n"
                "• ₿ Криптовалюты\n"
                "• 🌤️ Погода\n\n"
                "💡 <i>Следующие запросы будут использовать свежие данные</i>"
            )
        else:
            message = "❌ <b>Ошибка при обновлении кэша</b>"

        await update.message.reply_text(message, parse_mode='HTML')

        # Показываем обновленную статистику
        await cache_stats_command(update, context)

    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша: {e}")
        await update.message.reply_text("❌ Ошибка при обновлении кэша.")

async def preload_cache_data():
    """Предварительно загружает данные в кэш"""
    try:
        logger.info("🔄 Предварительная загрузка данных в кэш...")

        # 💱 Курсы валют
        try:
            from api_currency import get_currency_rates_with_history
            currency_data = get_currency_rates_with_history()
            logger.info("✅ Курсы валют загружены в кэш")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки курсов валют: {e}")

        # 💎 Ключевая ставка
        try:
            from api_keyrate import get_key_rate
            keyrate_data = get_key_rate()
            logger.info("✅ Ключевая ставка загружена в кэш")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки ключевой ставки: {e}")

        # 📊 RUONIA
        try:
            from api_ruonia import get_ruonia_rate
            ruonia_data = get_ruonia_rate()
            logger.info("✅ RUONIA загружена в кэш")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки RUONIA: {e}")

        # ₿ Криптовалюты
        try:
            from api_crypto import get_crypto_rates
            crypto_data = get_crypto_rates()
            logger.info("✅ Криптовалюты загружены в кэш")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки криптовалют: {e}")

        # 🌤️ Погода
        try:
            from api_weather import get_weather_moscow
            weather_data = get_weather_moscow()
            logger.info("✅ Погода загружена в кэш")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки погоды: {e}")

        logger.info("🎯 Предварительная загрузка кэша завершена")

    except Exception as e:
        logger.error(f"❌ Ошибка предварительной загрузки кэша: {e}")

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

        # 🔄 ПОКАЗЫВАЕМ СТАТИСТИКУ ПОСЛЕ ОЧИСТКИ
        await cache_stats_command(update, context)

    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {e}")
        await update.message.reply_text("❌ Ошибка при очистке кэша.")

# Добавляем новые функции в handlers_admin.py

async def cache_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает и позволяет редактировать расписание кэша"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        log_user_action(update.effective_user.id, "view_cache_schedule")

        from cache import get_cache_schedule, update_cache_schedule

        schedule = get_cache_schedule()

        message = "⏰ <b>РАСПИСАНИЕ ОБНОВЛЕНИЯ КЭША</b>\n\n"
        message += "<i>Текущее расписание (Московское время):</i>\n\n"

        for key, times in schedule.items():
            emoji = {
                'currency_rates': '💱',
                'key_rate': '💎',
                'ruonia_rate': '📊',
                'crypto_rates': '₿',
                'weather': '🌤️'
            }.get(key, '📝')

            key_name = {
                'currency_rates': 'Курсы валют',
                'key_rate': 'Ключевая ставка',
                'ruonia_rate': 'RUONIA',
                'crypto_rates': 'Криптовалюты',
                'weather': 'Погода'
            }.get(key, key)

            message += f"{emoji} <b>{key_name}:</b>\n"
            if times:
                message += f"   🕒 {', '.join(times)} МСК\n"
            else:
                message += f"   ⚠️ Не настроено\n"
            message += "\n"

        message += "💡 <b>Формат времени:</b> ЧЧ:ММ (24-часовой формат)\n"
        message += "📝 <b>Пример команды для изменения:</b>\n"
        message += "<code>/set_schedule currency_rates 07:00,10:00,13:00,16:00</code>\n\n"
        message += "🔄 <i>Используйте кнопки ниже для управления</i>"

        keyboard = [
            [KeyboardButton("💱 Изменить курс валют"), KeyboardButton("💎 Изменить ключевую ставку")],
            [KeyboardButton("📊 Изменить RUONIA"), KeyboardButton("₿ Изменить крипту")],
            [KeyboardButton("🌤️ Изменить погоду"), KeyboardButton("📊 Статистика кэша")],
            [KeyboardButton("🔙 Назад к админ-панели")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Ошибка при показе расписания кэша: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке расписания.")

async def set_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Устанавливает расписание для конкретного типа данных"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "📝 <b>Использование:</b>\n"
                "<code>/set_schedule &lt;тип&gt; &lt;время1&gt;,&lt;время2&gt;,...</code>\n\n"
                "💡 <b>Примеры:</b>\n"
                "<code>/set_schedule currency_rates 07:00,10:00,13:00,16:00,19:00</code>\n"
                "<code>/set_schedule key_rate 08:00</code>\n"
                "<code>/set_schedule ruonia_rate 08:00,12:00,16:00</code>\n"
                "<code>/set_schedule crypto_rates 09:00,12:00,15:00,18:00,21:00</code>\n"
                "<code>/set_schedule weather 06:00,12:00,18:00,22:00</code>\n\n"
                "📋 <b>Доступные типы:</b>\n"
                "• currency_rates - Курсы валют\n"
                "• key_rate - Ключевая ставка\n"
                "• ruonia_rate - RUONIA\n"
                "• crypto_rates - Криптовалюты\n"
                "• weather - Погода",
                parse_mode='HTML'
            )
            return

        key_type = context.args[0].lower()

        # 🔄 ИСПРАВЛЕНИЕ: Объединяем все оставшиеся аргументы в одну строку
        times_str = ' '.join(context.args[1:])

        # 🔄 ИСПРАВЛЕНИЕ: Разделяем по запятым и убираем лишние пробелы
        times = [t.strip() for t in times_str.split(',') if t.strip()]

        # Валидация типа
        valid_types = ['currency_rates', 'key_rate', 'ruonia_rate', 'crypto_rates', 'weather']
        if key_type not in valid_types:
            await update.message.reply_text(
                f"❌ Неверный тип данных. Доступные: {', '.join(valid_types)}"
            )
            return

        # 🔄 ИСПРАВЛЕНИЕ: Проверяем что есть хотя бы одно время
        if not times:
            await update.message.reply_text(
                "❌ Не указано ни одного времени.\n"
                "💡 Пример: <code>/set_schedule ruonia_rate 08:00,12:00,16:00</code>",
                parse_mode='HTML'
            )
            return

        # Валидация формата времени
        invalid_times = []
        valid_times = []

        for time_str in times:
            try:
                # Проверяем формат ЧЧ:ММ
                datetime.strptime(time_str, '%H:%M')
                valid_times.append(time_str)
            except ValueError:
                invalid_times.append(time_str)

        if invalid_times:
            await update.message.reply_text(
                f"❌ Неверный формат времени: {', '.join(invalid_times)}\n"
                "💡 Используйте формат ЧЧ:ММ (например, 08:00 или 14:30)"
            )
            return

        # 🔄 ИСПРАВЛЕНИЕ: Сортируем времена для удобства
        valid_times.sort()

        from cache import update_cache_schedule
        success = update_cache_schedule(key_type, valid_times)

        if success:
            key_names = {
                'currency_rates': 'Курсы валют',
                'key_rate': 'Ключевая ставка',
                'ruonia_rate': 'RUONIA',
                'crypto_rates': 'Криптовалюты',
                'weather': 'Погода'
            }

            message = (
                f"✅ <b>РАСПИСАНИЕ ОБНОВЛЕНО</b>\n\n"
                f"📝 <b>{key_names.get(key_type, key_type)}</b>\n"
                f"🕒 <b>Новое расписание:</b> {', '.join(valid_times)} МСК\n"
                f"📊 <b>Количество обновлений в день:</b> {len(valid_times)}\n\n"
                f"💡 <i>Кэш будет автоматически обновляться в указанное время</i>"
            )
        else:
            message = "❌ <b>Ошибка при обновлении расписания</b>"

        await update.message.reply_text(message, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Ошибка при установке расписания: {e}")
        await update.message.reply_text("❌ Ошибка при установке расписания.")

# В handlers_admin.py добавляем новые функции
async def user_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статистику использования бота пользователями"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        log_user_action(update.effective_user.id, "view_user_stats")

        # Получаем статистику за последние 30 дней
        stats = await get_user_actions_stats(30)

        if not stats or not stats.get('total_stats'):
            await update.message.reply_text(
                "📊 <b>СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
                "📭 <i>Нет данных для отображения</i>\n\n"
                "💡 <i>Статистика собирается с момента добавления этой функции</i>",
                parse_mode='HTML',
                reply_markup=create_user_stats_keyboard()
            )
            return

        total_stats = stats['total_stats']
        action_type_stats = stats['action_type_stats']
        popular_actions = stats['popular_actions']
        daily_activity = stats['daily_activity']
        active_users = stats['active_users']

        message = "📊 <b>СТАТИСТИКА ИСПОЛЬЗОВАНИЯ БОТА</b>\n\n"

        # Общая статистика
        message += "👥 <b>Общая статистика (30 дней):</b>\n"
        message += f"• Всего действий: <b>{total_stats.get('total_actions', 0)}</b>\n"
        message += f"• Уникальных пользователей: <b>{total_stats.get('unique_users', 0)}</b>\n"

        # Форматируем даты
        first_action = total_stats.get('first_action')
        last_action = total_stats.get('last_action')

        if first_action:
            first_action_str = first_action.strftime('%d.%m.%Y %H:%M') if hasattr(first_action, 'strftime') else str(first_action)
            message += f"• Первое действие: <b>{first_action_str}</b>\n"
        else:
            message += f"• Первое действие: <b>N/A</b>\n"

        if last_action:
            last_action_str = last_action.strftime('%d.%m.%Y %H:%M') if hasattr(last_action, 'strftime') else str(last_action)
            message += f"• Последнее действие: <b>{last_action_str}</b>\n"
        else:
            message += f"• Последнее действие: <b>N/A</b>\n"

        message += "\n"

        # Статистика по типам действий
        message += "🎯 <b>Действия по типам:</b>\n"
        for action_type in action_type_stats[:8]:  # Показываем топ-8
            emoji = {
                'view': '👀',
                'create': '➕',
                'delete': '🗑️',
                'update': '✏️',
                'system': '⚙️',
                'ai': '🤖',
                'alert': '🔔',
                'message': '💬'
            }.get(action_type['action_type'], '📝')

            type_name = {
                'view': 'Просмотры',
                'create': 'Создание',
                'delete': 'Удаление',
                'update': 'Обновление',
                'system': 'Системные',
                'ai': 'ИИ помощник',
                'alert': 'Уведомления',
                'message': 'Сообщения'
            }.get(action_type['action_type'], action_type['action_type'])

            message += f"{emoji} <b>{type_name}:</b> {action_type['action_count']} ({action_type['unique_users']} пользователей)\n"

        message += "\n"

        # Самые популярные действия
        message += "🔥 <b>Самые популярные действия:</b>\n"
        for i, action in enumerate(popular_actions[:5], 1):
            action_name = action['action_name'].replace('_', ' ').title()
            message += f"{i}. {action_name}: <b>{action['action_count']}</b> раз\n"

        message += "\n"

        # Самые активные пользователи
        message += "🏆 <b>Самые активные пользователи:</b>\n"
        for i, user in enumerate(active_users[:3], 1):
            user_info = f"User_{user['user_id']}"
            try:
                user_data = await get_user_info(user['user_id'])
                if user_data and user_data.get('username'):
                    user_info = f"@{user_data['username']}"
                elif user_data and user_data.get('first_name'):
                    user_info = user_data['first_name']
            except:
                pass

            message += f"{i}. {user_info}: <b>{user['action_count']}</b> действий\n"

        message += "\n💡 <i>Используйте кнопки ниже для детальной статистики</i>"

        await update.message.reply_text(
            message,
            parse_mode='HTML',
            reply_markup=create_user_stats_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка при показе статистики пользователей: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке статистики.")

async def detailed_user_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает детальную статистику по конкретному пользователю"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        if not context.args:
            await update.message.reply_text(
                "📝 <b>Использование:</b>\n"
                "<code>/user_detail &lt;user_id&gt;</code>\n\n"
                "💡 <b>Пример:</b>\n"
                "<code>/user_detail 661920</code>\n\n"
                "👥 <b>Чтобы получить ID пользователя:</b>\n"
                "Попросите пользователя отправить команду <code>/myid</code>",
                parse_mode='HTML'
            )
            return

        user_id = int(context.args[0])
        log_user_action(update.effective_user.id, "view_user_detail", {"target_user_id": user_id})

        # Получаем детальную статистику пользователя
        stats = await get_user_detailed_stats(user_id, 30)

        if not stats or not stats.get('user_stats'):
            await update.message.reply_text(
                f"❌ <b>Статистика не найдена</b>\n\n"
                f"Пользователь <b>{user_id}</b> не совершал действий за последние 30 дней.",
                parse_mode='HTML'
            )
            return

        user_stats = stats['user_stats']
        user_actions_by_type = stats['user_actions_by_type']
        recent_actions = stats['recent_actions']

        # Получаем информацию о пользователе
        user_info = "Неизвестный пользователь"
        try:
            user_data = await get_user_info(user_id)
            if user_data:
                username = f" @{user_data['username']}" if user_data.get('username') else ""
                user_info = f"{user_data.get('first_name', 'Пользователь')}{username}"
        except:
            pass

        message = f"👤 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n\n"
        message += f"<b>Пользователь:</b> {user_info} (ID: {user_id})\n\n"

        # Общая статистика
        message += "📈 <b>Общая активность (30 дней):</b>\n"
        message += f"• Всего действий: <b>{user_stats.get('total_actions', 0)}</b>\n"
        message += f"• Уникальных типов действий: <b>{user_stats.get('unique_action_types', 0)}</b>\n"
        message += f"• Уникальных действий: <b>{user_stats.get('unique_actions', 0)}</b>\n"

        # Форматируем даты
        first_action = user_stats.get('first_action')
        last_action = user_stats.get('last_action')

        if first_action:
            first_action_str = first_action.strftime('%d.%m.%Y %H:%M') if hasattr(first_action, 'strftime') else str(first_action)
            message += f"• Первое действие: <b>{first_action_str}</b>\n"
        else:
            message += f"• Первое действие: <b>N/A</b>\n"

        if last_action:
            last_action_str = last_action.strftime('%d.%m.%Y %H:%M') if hasattr(last_action, 'strftime') else str(last_action)
            message += f"• Последнее действие: <b>{last_action_str}</b>\n"
        else:
            message += f"• Последнее действие: <b>N/A</b>\n"

        message += "\n"

        # Действия по типам
        message += "🎯 <b>Действия по типам:</b>\n"
        for action_type in user_actions_by_type:
            type_name = {
                'view': '👀 Просмотры',
                'create': '➕ Создание',
                'delete': '🗑️ Удаление',
                'update': '✏️ Обновление',
                'system': '⚙️ Системные',
                'ai': '🤖 ИИ помощник',
                'alert': '🔔 Уведомления',
                'message': '💬 Сообщения'
            }.get(action_type['action_type'], f"📝 {action_type['action_type']}")

            message += f"• {type_name}: <b>{action_type['action_count']}</b> действий\n"

        message += "\n"

        # Последние действия
        message += "🕒 <b>Последние действия:</b>\n"
        for i, action in enumerate(recent_actions[:5], 1):
            action_name = action['action_name'].replace('_', ' ').title()
            action_time = action['created_at']

            if hasattr(action_time, 'strftime'):
                time_ago = datetime.now() - action_time
                hours_ago = int(time_ago.total_seconds() / 3600)

                if hours_ago < 1:
                    time_text = "только что"
                elif hours_ago < 24:
                    time_text = f"{hours_ago} ч. назад"
                else:
                    days = hours_ago // 24
                    time_text = f"{days} д. назад"
            else:
                time_text = "неизвестно"

            message += f"{i}. {action_name} - <i>{time_text}</i>\n"

        await update.message.reply_text(message, parse_mode='HTML')

    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID пользователя.")
    except Exception as e:
        logger.error(f"Ошибка при показе детальной статистики пользователя: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке статистики.")

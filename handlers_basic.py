# handlers_basic.py
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup  # Добавляем импорты
from telegram.ext import ContextTypes
from config import logger, ADMIN_IDS, BOT_VERSION, BOT_LAST_UPDATE, BOT_CREATION_DATE
from utils import log_user_action, create_main_reply_keyboard, create_other_functions_keyboard, create_admin_functions_keyboard
from db import update_user_info  # Добавляем импорт

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - только для первого запуска"""
    try:
        user = update.effective_user
        await update_user_info(user.id, user.first_name, user.username)  # Теперь функция доступна

        log_user_action(user.id, "start_bot")

        greeting = f"Привет, {user.first_name}!" if user.first_name else "Привет!"

        start_message = (
            f'{greeting}\n'
            f'Я бот для отслеживания финансовых данных и не только!\n\n'
            '💡 <b>Основные возможности:</b>\n'
            '• 💱 Курсы валют ЦБ РФ с прогнозом\n'
            '• ₿ Криптовалюты в реальном времени\n'
            '• 🏛️ Ставки ЦБ РФ (ключевая ставка и RUONIA)\n'
            '• 🤖 Универсальный ИИ помощник\n'
            '• 🔔 Умные уведомления\n'
            '• 🌅 Ежедневная рассылка\n\n'
            '👇 <b>Выберите действие в меню ниже:</b>'
        )

        # Проверяем доступность ИИ
        from config import DEEPSEEK_API_KEY
        if DEEPSEEK_API_KEY:
            try:
                from api_ai import ask_deepseek
                test_ai = await ask_deepseek("test", context, fast_check=True)
                ai_available = not (test_ai.startswith("❌") or test_ai.startswith("⏰"))
                if not ai_available:
                    start_message += "\n\n⚠️ <i>ИИ помощник временно недоступен</i>"
            except:
                start_message += "\n\n⚠️ <i>ИИ помощник временно недоступен</i>"

        reply_markup = create_main_reply_keyboard()
        await update.message.reply_text(start_message, parse_mode='HTML', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await show_main_menu(update, context)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /stop - прощание с пользователем"""
    try:
        user = update.effective_user
        user_name = user.first_name or "пользователь"

        log_user_action(user.id, "stop_command")

        stop_message = (
            f"👋 До свидания, {user_name}!\n\n"
            f"Бот завершил работу для вас.\n"
            f"Все ваши данные сохранены.\n\n"
            f"💡 Чтобы снова начать работу, используйте команду:\n"
            f"/start\n\n"
            f"📊 Ваши активные уведомления сохранены и будут проверяться.\n"
            f"🔔 Вы продолжите получать уведомления, если они сработают."
        )

        await update.message.reply_text(stop_message, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Ошибка в команде /stop: {e}")
        await update.message.reply_text("❌ Произошла ошибка при завершении работы.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "📚 <b>Доступные команды:</b>\n\n"

        "<b>Основные команды:</b>\n"
        "/start - Главное меню\n"
        "/stop - Завершить работу с ботом\n"
        "/rates - Курсы валют ЦБ РФ\n"
        "/crypto - Курсы криптовалют\n"
        "/keyrate - Ключевая ставка ЦБ РФ и RUONIA\n"
        "/ruonia - Ставка RUONIA\n"
        "/ruonia_history - История ставки RUONIA\n"
        "/ai - Чат с ИИ помощником\n"
        "/myalerts - Мои уведомления\n"
        "/alert - Создать уведомление\n"
        "/weather - Погода в Москве\n"
        "/status - Статус системы\n"
        "/help - Эта справка\n"
        "/myid - Показать мой ID\n"
    )

    if update.effective_user.id in ADMIN_IDS:
        help_text += (
            "\n👑 <b>Команды администратора:</b>\n"
            "/logs - Показать логи бота\n"
            "/clearlogs - Очистить логи\n"
        )

    help_text += (
        "\n💡 <b>Пример уведомления:</b>\n"
        "Бот уведомит когда USD превысит 80 руб.\n\n"

        "🌤️ <b>Погода:</b>\n"
        "Ежедневная рассылка в 10:00 МСК\n\n"

        "🏛️ <b>Ставки ЦБ РФ:</b>\n"
        "• Ключевая ставка\n"
        "• Ставка RUONIA\n"
        "• Сравнение ставок\n\n"

        "👇 <b>Или используйте кнопки меню ниже!</b>"
    )

    reply_markup = create_main_reply_keyboard()
    await update.message.reply_text(help_text, parse_mode='HTML', reply_markup=reply_markup)

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

async def show_other_functions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню прочих функций"""
    try:
        log_user_action(update.effective_user.id, "view_other_functions")

        message = (
            "🔧 <b>ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ</b>\n\n"
            "Выберите дополнительную функцию:\n\n"

            "🌤️ <b>Погода:</b>\n"
            "• Текущая погода в Москве\n"
            "• Ежедневная рассылка погоды\n"
            "• Рекомендации по одежде\n\n"

            "🏛️ <b>Ставки ЦБ РФ:</b>\n"
            "• Ключевая ставка\n"
            "• Ставка RUONIA\n"
            "• Сравнение ставок\n"
            "• Исторические данные\n\n"


            "⚙️ <b>Настройки:</b>\n"
            "• Настройка уведомлений\n"
            "• Выбор языка\n"
            "• Часовой пояс\n\n"

            "🔍 <b>Дополнительно:</b>\n"
            "• Информация о боте\n"
            "• Связь с разработчиком\n"
            "• Отзывы и предложения\n\n"
        )

        # Добавляем секцию для администраторов
        if update.effective_user.id in ADMIN_IDS:
            message += (
                "👑 <b>Административные функции:</b>\n"
                "• Просмотр системной статистики\n"
                "• Управление настройками бота\n"
                "• Доступ к логам системы\n\n"
            )

        message += "💡 <i>Новые функции добавляются регулярно!</i>"

        # Для администраторов показываем расширенную клавиатуру
        if update.effective_user.id in ADMIN_IDS:
            keyboard = [
                [KeyboardButton("🌤️ Погода"),
                [KeyboardButton("⚙️ Настройки"), KeyboardButton("ℹ️ О боте")],
                [KeyboardButton("👑 Админ-панель")],  # Новая кнопка для администраторов
                [KeyboardButton("🔙 Главное меню")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        else:
            reply_markup = create_other_functions_keyboard()

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Ошибка при показе прочих функций: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке функций.", reply_markup=create_main_reply_keyboard())

async def show_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статистику бота"""
    try:
        log_user_action(update.effective_user.id, "view_bot_stats")

        from db import get_all_users, get_all_alerts

        users = await get_all_users()
        alerts = await get_all_alerts()

        total_users = len(users)
        total_alerts = len(alerts)
        active_alerts = len([alert for alert in alerts if alert.get('is_active', True)])

        message = (
            "📊 <b>СТАТИСТИКА БОТА</b>\n\n"
            f"👥 <b>Всего пользователей:</b> {total_users}\n"
            f"🔔 <b>Всего уведомлений:</b> {total_alerts}\n"
            f"🟢 <b>Активных уведомлений:</b> {active_alerts}\n"
            f"🔴 <b>Выполненных уведомлений:</b> {total_alerts - active_alerts}\n\n"

            "📈 <b>Популярные валюты для уведомлений:</b>\n"
        )

        currency_stats = {}
        for alert in alerts:
            currency = alert['from_currency']
            currency_stats[currency] = currency_stats.get(currency, 0) + 1

        if currency_stats:
            sorted_currencies = sorted(currency_stats.items(), key=lambda x: x[1], reverse=True)
            for currency, count in sorted_currencies[:5]:
                message += f"   • {currency}: {count} уведомлений\n"
        else:
            message += "   <i>Нет данных</i>\n"

        message += "\n💡 <i>Статистика обновляется в реальном времени</i>"

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_other_functions_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе статистики: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке статистики.", reply_markup=create_other_functions_keyboard())

async def show_bot_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает информацию о боте"""
    try:
        log_user_action(update.effective_user.id, "view_bot_about")

        message = (
            "ℹ️ <b>ИНФОРМАЦИЯ О БОТЕ</b>\n\n"

            "🤖 <b>Финансовый бот с ИИ помощником</b>\n\n"

            "📚 <b>Основные возможности:</b>\n"
            "• 💱 Курсы валют ЦБ РФ с прогнозом\n"
            "• ₿ Криптовалюты через CoinGecko API\n"
            "• 🏛️ Ставки ЦБ РФ (ключевая ставка и RUONIA)\n"
            "• 🤖 Универсальный ИИ помощник\n"
            "• 🔔 Умные уведомления\n"
            "• 🌅 Ежедневная рассылка\n\n"

            "🛠 <b>Технологии:</b>\n"
            "• Python 3.8+\n"
            "• PostgreSQL\n"
            "• python-telegram-bot\n"
            "• DeepSeek AI API\n"
            "• CoinGecko API\n"
            "• ЦБ РФ API\n\n"

            "📞 <b>Поддержка:</b>\n"
            "• Для связи с разработчиком и сообщения об ошибках: korin2008@ya.ru\n"
            "Собрал данного бота Санёк\n\n"

            f"💡 <b>Версия:</b> {BOT_VERSION}\n"
            f"🔄 <b>Последнее обновление:</b> {BOT_LAST_UPDATE}\n"
            f"📅 <b>Создан:</b> {BOT_CREATION_DATE}\n\n"

            f"⭐ <i>Бот (создан в {BOT_CREATION_DATE.lower()}) постоянно развивается и улучшается!</i>"
        )

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_other_functions_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе информации о боте: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке информации.", reply_markup=create_other_functions_keyboard())

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает настройки"""
    try:
        log_user_action(update.effective_user.id, "view_settings")

        message = (
            "⚙️ <b>НАСТРОЙКИ</b>\n\n"

            "🔔 <b>Уведомления:</b>\n"
            "• Ежедневная рассылка: <b>Включено</b>\n"
            "• Погода: <b>Включено</b>\n"
            "• Курсы валют: <b>Включено</b>\n"
            "• Проверка уведомлений: <b>Каждые 30 минут</b>\n\n"

            "🌤️ <b>Погода:</b>\n"
            "• Город: <b>Москва</b>\n"
            "• Ежедневная рассылка: <b>10:00</b>\n"
            "• Единицы измерения: <b>°C, м/с</b>\n\n"

            "🌍 <b>Региональные настройки:</b>\n"
            "• Часовой пояс: <b>Москва (UTC+3)</b>\n"
            "• Язык: <b>Русский</b>\n\n"

            "📊 <b>Отображение:</b>\n"
            "• Формат чисел: <b>С разделителями</b>\n"
            "• Валюта по умолчанию: <b>RUB</b>\n\n"

            "💡 <i>Настройки будут доступны для изменения в будущих обновлениях</i>"
        )

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_other_functions_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе настроек: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке настроек.", reply_markup=create_other_functions_keyboard())

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает ID пользователя"""
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 Ваш ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.first_name or 'Не указано'}\n"
        f"📛 Username: @{user.username or 'Не указан'}",
        parse_mode='HTML',
        reply_markup=create_main_reply_keyboard()
    )

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает административную панель (только для администраторов)"""
    try:
        # Проверяем права администратора
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text(
                "❌ У вас нет доступа к этой функции.",
                reply_markup=create_other_functions_keyboard()
            )
            return

        log_user_action(update.effective_user.id, "view_admin_panel")

        # Получаем системную информацию
        import psutil
        import platform
        from datetime import datetime
        from db import get_all_users, get_all_alerts

        users = await get_all_users()
        alerts = await get_all_alerts()
        active_alerts = len([alert for alert in alerts if alert.get('is_active', True)])

        # Системная информация
        system_info = (
            "👑 <b>АДМИНИСТРАТИВНАЯ ПАНЕЛЬ</b>\n\n"

            "🖥️ <b>Системная информация:</b>\n"
            f"• OS: {platform.system()} {platform.release()}\n"
            f"• Python: {platform.python_version()}\n"
            f"• CPU: {psutil.cpu_percent()}%\n"
            f"• Memory: {psutil.virtual_memory().percent}%\n"
            f"• Disk: {psutil.disk_usage('/').percent}%\n\n"

            "🤖 <b>Статистика бота:</b>\n"
            f"• Пользователей: {len(users)}\n"
            f"• Всего уведомлений: {len(alerts)}\n"
            f"• Активных уведомлений: {active_alerts}\n"
            f"• Администраторов: {len(ADMIN_IDS)}\n\n"

            "📊 <b>API статусы:</b>\n"
        )

        # Проверяем статусы API
        from api_currency import get_currency_rates_for_date
        from api_crypto import get_crypto_rates
        from config import DEEPSEEK_API_KEY, WEATHER_API_KEY, COINGECKO_API_KEY

        # ЦБ РФ
        try:
            rates, _ = get_currency_rates_for_date(datetime.now().strftime('%d/%m/%Y'))
            system_info += "• ЦБ РФ: ✅ Работает\n"
        except:
            system_info += "• ЦБ РФ: ❌ Ошибка\n"

        # CoinGecko
        crypto_data = get_crypto_rates()
        if crypto_data and crypto_data.get('source') == 'coingecko':
            system_info += f"• CoinGecko: ✅ Работает ({'API ключ' if COINGECKO_API_KEY else 'бесплатно'})\n"
        else:
            system_info += f"• CoinGecko: ❌ Ошибка\n"

        # DeepSeek
        system_info += f"• DeepSeek AI: {'✅ Доступен' if DEEPSEEK_API_KEY else '❌ Не настроен'}\n"

        # Погода
        system_info += f"• Погода: {'✅ Настроена' if WEATHER_API_KEY and WEATHER_API_KEY != 'demo_key_12345' else '⚠️ Демо-данные'}\n\n"

        system_info += (
            "💡 <b>Доступные команды:</b>\n"
            "/status - Детальный статус системы\n"
            "/logs - Просмотр логов\n"
            "/clearlogs - Очистка логов\n\n"

            "🔒 <i>Эта панель доступна только администраторам</i>"
        )

        await update.message.reply_text(system_info, parse_mode='HTML', reply_markup=create_admin_functions_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе административной панели: {e}")
        await update.message.reply_text(
            "❌ Ошибка при загрузке административной панели.",
            reply_markup=create_other_functions_keyboard()
        )

async def show_system_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает детальную статистику системы (только для администраторов)"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        log_user_action(update.effective_user.id, "view_system_stats")

        from db import get_all_users, get_all_alerts
        import psutil
        from datetime import datetime

        users = await get_all_users()
        alerts = await get_all_alerts()

        # Анализируем уведомления по валютам
        currency_stats = {}
        for alert in alerts:
            currency = alert['from_currency']
            currency_stats[currency] = currency_stats.get(currency, 0) + 1

        # Сортируем по популярности
        popular_currencies = sorted(currency_stats.items(), key=lambda x: x[1], reverse=True)[:5]

        message = (
            "📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА СИСТЕМЫ</b>\n\n"

            "👥 <b>Пользователи:</b>\n"
            f"• Всего пользователей: {len(users)}\n\n"

            "🔔 <b>Уведомления:</b>\n"
            f"• Всего уведомлений: {len(alerts)}\n"
            f"• Активных уведомлений: {len([a for a in alerts if a.get('is_active', True)])}\n\n"

            "💱 <b>Популярные валюты для уведомлений:</b>\n"
        )

        for currency, count in popular_currencies:
            message += f"• {currency}: {count} уведомлений\n"

        if not popular_currencies:
            message += "• Нет данных\n"

        message += f"\n🕒 <b>Время сервера:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        message += f"💾 <b>Использование памяти:</b> {psutil.virtual_memory().percent}%\n"
        message += f"🔧 <b>Загрузка CPU:</b> {psutil.cpu_percent()}%\n\n"

        message += "📈 <i>Статистика обновляется в реальном времени</i>"

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_admin_functions_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе статистики системы: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке статистики.")

async def show_bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает настройки бота (только для администраторов)"""
    try:
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этой функции.")
            return

        log_user_action(update.effective_user.id, "view_bot_settings")

        from config import DEEPSEEK_API_KEY, WEATHER_API_KEY, COINGECKO_API_KEY

        message = (
            "⚙️ <b>НАСТРОЙКИ БОТА</b>\n\n"

            "📋 <b>Основные настройки:</b>\n"
            f"• Версия: {BOT_VERSION}\n"
            f"• Последнее обновление: {BOT_LAST_UPDATE}\n"
            f"• Дата создания: {BOT_CREATION_DATE}\n\n"

            "🔑 <b>API ключи:</b>\n"
            f"• DeepSeek AI: {'✅ Настроен' if DEEPSEEK_API_KEY else '❌ Не настроен'}\n"
            f"• Погода: {'✅ Настроен' if WEATHER_API_KEY and WEATHER_API_KEY != 'demo_key_12345' else '❌ Не настроен'}\n"
            f"• CoinGecko: {'✅ Настроен' if COINGECKO_API_KEY else '❌ Не настроен'}\n\n"

            "⏰ <b>Расписание задач:</b>\n"
            "• Ежедневная рассылка курсов: 15:00 МСК\n"
            "• Ежедневная рассылка погоды: 10:00 МСК\n"
            "• Проверка уведомлений: каждые 30 минут\n\n"

            "💡 <i>Настройки управляются через переменные окружения</i>"
        )

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_admin_functions_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе настроек бота: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке настроек.")
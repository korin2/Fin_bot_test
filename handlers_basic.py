import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import logger, DEEPSEEK_API_KEY
from utils import log_user_action, create_main_reply_keyboard
# Обновляем импорт
from api_ai import ask_deepseek
from db import update_user_info


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - только для первого запуска"""
    try:
        user = update.effective_user
        await update_user_info(user.id, user.first_name, user.username)

        log_user_action(user.id, "start_bot")

        greeting = f"Привет, {user.first_name}!" if user.first_name else "Привет!"

        start_message = (
            f'{greeting}\n'
            f'Я бот для отслеживания финансовых данных и не только!\n\n'
            '💡 <b>Основные возможности:</b>\n'
            '• 💱 Курсы валют ЦБ РФ с прогнозом\n'
            '• ₿ Криптовалюты в реальном времени\n'
            '• 💎 Ключевая ставка ЦБ РФ\n'
            '• 🤖 Универсальный ИИ помощник\n'
            '• 🔔 Умные уведомления\n'
            '• 🌤️ Погода в Москве\n\n'
            '👇 <b>Выберите действие в меню ниже:</b>'
        )

        # Проверяем доступность ИИ
        if DEEPSEEK_API_KEY:
            try:
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

# handlers_basic.py - исправляем help_command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    from config import ADMIN_IDS

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
        "\n 🏛️ <b>Ставки ЦБ РФ:</b>\n"
        "• Ключевая ставка\n"
        "• Ставка RUONIA\n"
        "• Сравнение ставок\n\n"

        "💡 <b>Пример уведомления:</b>\n"
        "Бот уведомит когда USD превысит 80 руб.\n\n"

        "🌤️ <b>Погода:</b>\n"
        "Ежедневная рассылка в 10:00 МСК\n\n"

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

# handlers_basic.py - обновляем show_other_functions
async def show_other_functions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню прочих функций"""
    try:
        log_user_action(update.effective_user.id, "view_other_functions")

        message = (
            "🔧 <b>ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ</b>\n\n"
            "Выберите дополнительную функцию:\n\n"

            "🏛️ <b>Ставки ЦБ РФ:</b>\n"  # Обновляем описание
            "• Ключевая ставка\n"
            "• Ставка RUONIA\n"
            "• Сравнение ставок\n"
            "• Исторические данные\n\n"

            "📊 <b>Аналитика:</b>\n"
            "• Статистика использования бота\n"
            "• Графики изменения курсов\n"
            "• Исторические данные\n\n"

            "🌤️ <b>Погода:</b>\n"
            "• Текущая погода в Москве\n"
            "• Ежедневная рассылка погоды\n"
            "• Рекомендации по одежде\n\n"

            "⚙️ <b>Настройки:</b>\n"
            "• Настройка уведомлений\n"
            "• Выбор языка\n"
            "• Часовой пояс\n\n"

            "🔍 <b>Дополнительно:</b>\n"
            "• Информация о боте\n"
            "• Связь с разработчиком\n"
            "• Отзывы и предложения\n\n"

            "💡 <i>Новые функции добавляются регулярно!</i>"
        )

        from utils import create_other_functions_keyboard
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

        from utils import create_other_functions_keyboard
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=create_other_functions_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при показе статистики: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке статистики.", reply_markup=create_other_functions_keyboard())

# handlers_basic.py - обновляем show_bot_about
async def show_bot_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает информацию о боте"""
    try:
        log_user_action(update.effective_user.id, "view_bot_about")

        from config import BOT_VERSION, BOT_LAST_UPDATE, BOT_CREATION_DATE

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

        from utils import create_other_functions_keyboard
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

        from utils import create_other_functions_keyboard
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

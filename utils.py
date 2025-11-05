import logging
import json
from datetime import datetime
from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)

async def split_long_message(text: str, max_length: int = 4096) -> list:
    """Разбивает длинное сообщение на части для Telegram"""
    if len(text) <= max_length:
        return [text]

    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break

        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind('.', 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, max_length)
        if split_pos == -1:
            split_pos = max_length

        parts.append(text[:split_pos + 1])
        text = text[split_pos + 1:]

    return parts

def create_back_button():
    """Создает кнопку 'Назад в меню'"""
    from telegram import InlineKeyboardButton
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_main')]])

def log_user_action(user_id: int, action: str, details: dict = None):
    """Логирование действий пользователя"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'action': action,
        'details': details or {}
    }
    logger.info(f"USER_ACTION: {json.dumps(log_entry)}")

def create_main_reply_keyboard():
    """Создает главное reply-меню"""
    keyboard = [
        [
            KeyboardButton("💱 Курсы валют"),
            KeyboardButton("₿ Криптовалюты")
        ],
        [
            KeyboardButton("🏛️ Ставки ЦБ РФ"),
            KeyboardButton("🤖 ИИ помощник")
        ],
        [
            KeyboardButton("🔔 Уведомления"),

        ],
        [
            KeyboardButton("🔧 Другие функции"),
            KeyboardButton("❓ Помощь")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_other_functions_keyboard():
    """Создает клавиатуру для раздела 'Другие функции'"""
    keyboard = [
        [
            KeyboardButton("🌤️ Погода"),

        ],
        [
            KeyboardButton("⚙️ Настройки"),
            KeyboardButton("ℹ️ О боте")
        ],
        [
            KeyboardButton("🔙 Главное меню")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_ai_keyboard():
    """Создает клавиатуру для режима ИИ"""
    keyboard = [
        [KeyboardButton("💡 Примеры вопросов")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_alerts_keyboard():
    """Создает клавиатуру для раздела уведомлений"""
    keyboard = [
        [KeyboardButton("💱 Создать уведомление")],
        [KeyboardButton("📋 Мои уведомления")],
        [KeyboardButton("🌤️ Погода (вкл/выкл)")],  # Новая кнопка
        [KeyboardButton("🗑 Очистить все уведомления")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_currency_selection_keyboard():
    """Создает клавиатуру для выбора валюты"""
    from config import SUPPORTED_CURRENCIES

    keyboard = []
    row = []

    for i, currency in enumerate(SUPPORTED_CURRENCIES):
        row.append(KeyboardButton(currency))
        if len(row) == 3 or i == len(SUPPORTED_CURRENCIES) - 1:
            keyboard.append(row)
            row = []

    keyboard.append([KeyboardButton("🔙 Назад к уведомлениям")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_alert_direction_keyboard():
    """Создает клавиатуру для выбора направления уведомления"""
    keyboard = [
        [KeyboardButton("📈 Выше порога"), KeyboardButton("📉 Ниже порога")],
        [KeyboardButton("🔙 Назад к валютам")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def create_admin_functions_keyboard():
    """Создает клавиатуру для административных функций"""
    keyboard = [
        [KeyboardButton("📊 Статистика системы")],
        [KeyboardButton("💾 Статистика кэша")],  # Новая кнопка
        [KeyboardButton("🔧 Настройки бота")],
        [KeyboardButton("📋 Логи бота")],
        [KeyboardButton("🔙 Назад к функциям")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def create_cache_management_keyboard():
    """Создает клавиатуру для управления кэшем"""
    keyboard = [
        [KeyboardButton("🔄 Обновить кэш")],
        [KeyboardButton("🧹 Очистить кэш")],
        [KeyboardButton("📊 Обновить статистику")],
        [KeyboardButton("🔙 Назад к админ-панели")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

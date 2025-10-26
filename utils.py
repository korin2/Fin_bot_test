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
            KeyboardButton("💎 Ключевая ставка"), 
            KeyboardButton("🤖 ИИ помощник")
        ],
        [
            KeyboardButton("🔔 Уведомления"), 
            KeyboardButton("🌤️ Погода")
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
            KeyboardButton("📊 Статистика"), 
            KeyboardButton("⚙️ Настройки")
        ],
        [
            KeyboardButton("ℹ️ О боте"), 
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
        [KeyboardButton("🗑 Очистить все уведомления")],
        [KeyboardButton("💱 Создать уведомление")],
        [KeyboardButton("🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import logger, DEEPSEEK_API_KEY
from utils import log_user_action, create_ai_keyboard, create_main_reply_keyboard, split_long_message
# Обновляем импорт
from api_ai import ask_deepseek

async def show_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает интерфейс чата с ИИ"""
    try:
        log_user_action(update.effective_user.id, "start_ai_chat")
        
        if not DEEPSEEK_API_KEY:
            error_msg = "❌ <b>Функционал ИИ временно недоступен</b>"
            await update.message.reply_text(error_msg, parse_mode='HTML', reply_markup=create_main_reply_keyboard())
            return
        
        # Активируем режим ИИ для пользователя
        context.user_data['ai_mode'] = True
        
        welcome_message = (
            "🤖 <b>УНИВЕРСАЛЬНЫЙ ИИ ПОМОЩНИК</b>\n\n"
            "Задайте мне любой вопрос по любой теме!\n\n"
            "🎯 <b>Основные направления:</b>\n"
            "• 💰 Финансы и инвестиции\n"
            "• 📊 Технологии и программирование\n"
            "• 🎓 Образование и наука\n"
            "• 🎨 Творчество и искусство\n"
            "• 🏥 Здоровье и спорт\n"
            "• 🌍 Путешествия и культура\n"
            "• 🔧 Советы и решение проблем\n"
            "• 💬 Общение и поддержка\n\n"
            "Просто напишите ваш вопрос в чат!\n\n"
            "<i>Для выхода из режима ИИ используйте кнопку 'Главное меню'</i>"
        )
        
        reply_markup = create_ai_keyboard()
        await update.message.reply_text(welcome_message, parse_mode='HTML', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Ошибка при показе чата с ИИ: {e}")
        await update.message.reply_text("❌ Ошибка при запуске ИИ помощника.", reply_markup=create_main_reply_keyboard())

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения для ИИ"""
    try:
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Проверяем, не является ли сообщение командой
        if user_message.startswith('/'):
            return
            
        # Проверяем, активирован ли режим ИИ для пользователя
        if context.user_data.get('ai_mode') != True:
            return
            
        # Логируем запрос к ИИ
        log_user_action(user_id, "ai_request", {"message_length": len(user_message)})
        
        # Показываем индикатор набора сообщения
        await update.message.chat.send_action(action="typing")
        
        # Отправляем запрос к DeepSeek
        ai_response = await ask_deepseek(user_message, context)
        
        # Разбиваем длинные сообщения на части
        message_parts = await split_long_message(ai_response)
        
        # Отправляем первую часть с клавиатурой
        first_part = message_parts[0]
        if len(message_parts) > 1:
            first_part += f"\n\n📄 <i>Часть 1 из {len(message_parts)}</i>"
        
        keyboard = [
            [KeyboardButton("🔄 Новый вопрос")],
            [KeyboardButton("🔙 Главное меню")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"🤖 <b>ИИ Ассистент:</b>\n\n{first_part}",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        # Отправляем остальные части
        for i, part in enumerate(message_parts[1:], 2):
            part_text = part
            if i < len(message_parts):
                part_text += f"\n\n📄 <i>Часть {i} из {len(message_parts)}</i>"
            
            await update.message.reply_text(
                part_text,
                parse_mode='HTML'
            )
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике ИИ сообщений: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке вашего запроса.",
            reply_markup=create_main_reply_keyboard()
        )

async def show_ai_examples(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает примеры вопросов для ИИ"""
    examples_text = (
        "💡 <b>ПРИМЕРЫ ВОПРОСОВ ДЛЯ ИИ:</b>\n\n"
        "💰 <b>Финансы:</b>\n"
        "• Как начать инвестировать с маленькой суммой?\n"
        "• Каков прогноз курса доллара на месяц?\n"
        "• В чем разница между акциями и облигациями?\n\n"
        "📊 <b>Технологии:</b>\n"
        "• Объясни что такое блокчейн простыми словами\n"
        "• Как создать телеграм бота на Python?\n"
        "• Какие языки программирования учить в 2024?\n\n"
        "🎓 <b>Образование:</b>\n"
        "• Как эффективно учиться новому?\n"
        "• Объясни теорию относительности Эйнштейна\n"
        "• Какие навыки будут востребованы в будущем?\n\n"
        "🎨 <b>Творчество:</b>\n"
        "• Придумай идею для стартапа в IT\n"
        "• Напиши короткое стихотворение о технологии\n"
        "• Какие тренды в дизайне сейчас популярны?\n\n"
        "🏥 <b>Здоровье:</b>\n"
        "• Как поддерживать здоровый образ жизни?\n"
        "• Какие упражнения делать при сидячей работе?\n"
        "• Как бороться со стрессом на работе?\n\n"
        "🌍 <b>Путешествия:</b>\n"
        "• Куда поехать отдыхать с ограниченным бюджетом?\n"
        "• Какие документы нужны для поездки в Европу?\n"
        "• Как путешествовать экологично?\n\n"
        "💬 <b>Просто поговорить:</b>\n"
        "• Расскажи интересный факт о космосе\n"
        "• Что думаешь об искусственном интеллекте?\n"
        "• Давай обсудим будущее технологий"
    )
    await update.message.reply_text(
        examples_text,
        parse_mode='HTML',
        reply_markup=create_ai_keyboard()
    )

# admin_panel.py - исправляем импорты
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import logger, ADMIN_IDS
from utils import log_user_action, create_admin_functions_keyboard
from smart_cache import cache_manager

class AdminCacheManager:
    """
    Класс для управления кэшем через админ-панель
    """

    def __init__(self):
        # Функции для получения данных каждого типа
        self.fetch_functions = {
            'ruonia': self._get_ruonia_rate,
            'ruonia_historical_30': self._get_ruonia_historical,
            'key_rate': self._get_key_rate,
            'currency': self._get_currency_rates
        }

    def _get_ruonia_rate(self):
        """Получает ставку RUONIA без кэша"""
        try:
            from api_ruonia import get_ruonia_rate
            return get_ruonia_rate(use_cache=False)
        except Exception as e:
            logger.error(f"Ошибка получения ruonia: {e}")
            return None

    def _get_ruonia_historical(self):
        """Получает историю RUONIA без кэша"""
        try:
            from api_ruonia import get_ruonia_historical
            return get_ruonia_historical(days=30, use_cache=False)
        except Exception as e:
            logger.error(f"Ошибка получения ruonia historical: {e}")
            return None

    def _get_key_rate(self):
        """Получает ключевую ставку без кэша"""
        try:
            from api_keyrate import get_key_rate
            return get_key_rate()
        except Exception as e:
            logger.error(f"Ошибка получения key rate: {e}")
            return None

    def _get_currency_rates(self):
        """Получает курсы валют без кэша"""
        try:
            from api_currency import get_currency_rates_with_history
            rates_today, date_today, _, _, _, _ = get_currency_rates_with_history()
            return rates_today
        except Exception as e:
            logger.error(f"Ошибка получения currency rates: {e}")
            return None

    async def show_cache_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает панель управления кэшем"""
        try:
            if update.effective_user.id not in ADMIN_IDS:
                await update.message.reply_text("❌ У вас нет доступа к этой функции.")
                return

            log_user_action(update.effective_user.id, "view_cache_management")

            # Получаем информацию о кэше
            cache_info = cache_manager.get_cache_info()

            message = "💾 <b>УПРАВЛЕНИЕ КЭШЕМ</b>\n\n"

            if cache_info:
                message += "📊 <b>Текущее состояние кэша:</b>\n"
                for data_type, info in cache_info.items():
                    status_icon = "🟢" if not info['needs_refresh'] else "🟡"
                    message += (
                        f"{status_icon} <b>{data_type}:</b>\n"
                        f"   • Возраст: {info['age_str']}\n"
                        f"   • Время: {info['timestamp']}\n"
                        f"   • Статус: {info['status']}\n\n"
                    )
            else:
                message += "📭 <b>Кэш пуст</b>\n\n"

            message += (
                "🔄 <b>Доступные действия:</b>\n"
                "• <b>Обновить весь кэш</b> - принудительное обновление всех данных\n"
                "• <b>Обновить RUONIA</b> - обновить только ставку RUONIA\n"
                "• <b>Обновить валюты</b> - обновить только курсы валют\n"
                "• <b>Очистить кэш</b> - полная очистка кэша\n"
                "• <b>Статус кэша</b> - подробная информация о кэше\n\n"

                "💡 <i>Кэш автоматически обновляется по расписанию и при истечении TTL</i>"
            )

            keyboard = [
                [KeyboardButton("🔄 Обновить весь кэш"), KeyboardButton("📊 Статус кэша")],
                [KeyboardButton("🔄 RUONIA"), KeyboardButton("🔄 Валюты")],
                [KeyboardButton("🗑️ Очистить кэш"), KeyboardButton("🔙 Назад к админ-панели")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Ошибка при показе управления кэшем: {e}")
            await update.message.reply_text(
                "❌ Ошибка при загрузке управления кэшем.",
                reply_markup=create_admin_functions_keyboard()
            )

    async def handle_cache_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
        """Обрабатывает команды управления кэшем"""
        try:
            if update.effective_user.id not in ADMIN_IDS:
                await update.message.reply_text("❌ У вас нет доступа к этой функции.")
                return

            user_id = update.effective_user.id

            if command == "🔄 Обновить весь кэш":
                log_user_action(user_id, "refresh_all_cache")
                await self._refresh_all_cache(update)

            elif command == "📊 Статус кэша":
                log_user_action(user_id, "view_cache_status")
                await self._show_cache_status(update)

            elif command == "🔄 RUONIA":
                log_user_action(user_id, "refresh_ruonia_cache")
                await self._refresh_specific_cache(update, 'ruonia')

            elif command == "🔄 Валюты":
                log_user_action(user_id, "refresh_currency_cache")
                await self._refresh_specific_cache(update, 'currency')

            elif command == "🗑️ Очистить кэш":
                log_user_action(user_id, "clear_all_cache")
                await self._clear_all_cache(update)

            elif command == "🔙 Назад к админ-панели":
                from handlers_basic import show_admin_panel
                await show_admin_panel(update, context)

        except Exception as e:
            logger.error(f"Ошибка при обработке команды кэша '{command}': {e}")
            await update.message.reply_text(
                f"❌ Ошибка при выполнении команды: {e}",
                reply_markup=create_admin_functions_keyboard()
            )

    async def _refresh_all_cache(self, update: Update) -> None:
        """Обновляет весь кэш"""
        await update.message.reply_text("🔄 <b>Обновление всего кэша...</b>", parse_mode='HTML')

        results = cache_manager.force_refresh_all(self.fetch_functions)

        message = "✅ <b>РЕЗУЛЬТАТЫ ОБНОВЛЕНИЯ КЭША</b>\n\n"

        success_count = 0
        for data_type, result in results.items():
            if result['status'] == 'success':
                message += f"🟢 <b>{data_type}:</b> Успешно обновлено\n"
                success_count += 1
            else:
                message += f"🔴 <b>{data_type}:</b> Ошибка: {result['error']}\n"

        message += f"\n📊 Итого: {success_count}/{len(results)} успешно\n"
        message += "💾 Кэш сохранен на диск"

        await update.message.reply_text(message, parse_mode='HTML')

    async def _refresh_specific_cache(self, update: Update, data_type: str) -> None:
        """Обновляет конкретный тип данных в кэше"""
        if data_type not in self.fetch_functions:
            await update.message.reply_text(f"❌ Неизвестный тип данных: {data_type}")
            return

        await update.message.reply_text(f"🔄 <b>Обновление {data_type}...</b>", parse_mode='HTML')

        result = cache_manager.force_refresh_specific(data_type, self.fetch_functions[data_type])

        if result['status'] == 'success':
            message = (
                f"✅ <b>{data_type.upper()} ОБНОВЛЕН</b>\n\n"
                f"💾 Данные успешно обновлены и сохранены в кэш\n"
                f"🕒 Время: {cache_manager.cache[data_type]['timestamp'].strftime('%d.%m.%Y %H:%M:%S')}"
            )
        else:
            message = f"❌ <b>ОШИБКА ОБНОВЛЕНИЯ {data_type.upper()}</b>\n\n{result['error']}"

        await update.message.reply_text(message, parse_mode='HTML')

    async def _clear_all_cache(self, update: Update) -> None:
        """Очищает весь кэш"""
        result = cache_manager.clear_cache()

        message = (
            "🗑️ <b>КЭШ ОЧИЩЕН</b>\n\n"
            f"{result}\n\n"
            "💡 Все данные будут загружены заново при следующем запросе"
        )

        await update.message.reply_text(message, parse_mode='HTML')

    async def _show_cache_status(self, update: Update) -> None:
        """Показывает подробный статус кэша"""
        cache_info = cache_manager.get_cache_info()

        if not cache_info:
            await update.message.reply_text("📭 <b>Кэш пуст</b>", parse_mode='HTML')
            return

        message = "📊 <b>ПОДРОБНЫЙ СТАТУС КЭША</b>\n\n"

        for data_type, info in cache_info.items():
            status_icon = "🟢" if not info['needs_refresh'] else "🟡"
            refresh_status = "Актуален" if not info['needs_refresh'] else "Требует обновления"

            message += (
                f"{status_icon} <b>{data_type.upper()}</b>\n"
                f"   • Возраст: {info['age_str']} ({info['age_hours']} ч)\n"
                f"   • Время обновления: {info['timestamp']}\n"
                f"   • Статус: {refresh_status}\n"
                f"   • Данные: {'✅ Присутствуют' if info['data_exists'] else '❌ Отсутствуют'}\n\n"
            )

        # Добавляем информацию о расписании
        message += "⏰ <b>Расписание обновления:</b>\n"
        for data_type, schedule in cache_manager.schedule.items():
            message += f"   • {data_type}: {', '.join(schedule)}\n"

        message += "\n⏳ <b>TTL (в часах):</b>\n"
        for data_type, ttl in cache_manager.ttl_hours.items():
            message += f"   • {data_type}: {ttl} ч\n"

        message += "\n💡 <i>Кэш автоматически сохраняется на диск</i>"

        await update.message.reply_text(message, parse_mode='HTML')

# Создаем глобальный экземпляр
admin_cache_manager = AdminCacheManager()

# Функции для импорта в другие модули
async def show_cache_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает панель управления кэшем"""
    await admin_cache_manager.show_cache_management(update, context)

async def handle_cache_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    """Обрабатывает команды управления кэшем"""
    await admin_cache_manager.handle_cache_command(update, context, command)
# admin_panel.py
from smart_cache import cache_manager
from api_ruonia import get_ruonia_rate, get_ruonia_historical
from api_key_rate import get_key_rate  # предположим, что есть такой модуль
from api_currency import get_currency_rates  # предположим, что есть такой модуль
import logging
from config import logger

class AdminCacheManager:
    """
    Класс для управления кэшем через админ-панель
    """

    def __init__(self):
        # Функции для получения данных каждого типа
        self.fetch_functions = {
            'ruonia': lambda: get_ruonia_rate(use_cache=False),
            'ruonia_historical_30': lambda: get_ruonia_historical(30, use_cache=False),
            'key_rate': lambda: get_key_rate(use_cache=False),  # добавите свою функцию
            'currency': lambda: get_currency_rates(use_cache=False)  # добавите свою функцию
        }

    def get_cache_status_message(self):
        """
        Форматирует сообщение со статусом кэша для админа
        """
        cache_info = cache_manager.get_cache_info()

        if not cache_info:
            return "❌ Кэш пуст"

        message = "🔧 <b>СТАТУС КЭША</b>\n\n"

        for data_type, info in cache_info.items():
            status_icon = "🟢" if not info['needs_refresh'] else "🟡"
            message += f"{status_icon} <b>{data_type}:</b>\n"
            message += f"   📅 Возраст: {info['age_str']}\n"
            message += f"   🕒 Время: {info['timestamp']}\n"
            message += f"   📊 Статус: {info['status']}\n"

            if info['data_exists']:
                message += f"   ✅ Данные: присутствуют\n"
            else:
                message += f"   ❌ Данные: отсутствуют\n"

            message += "\n"

        message += f"📊 Всего записей в кэше: <b>{len(cache_info)}</b>"

        return message

    def force_refresh_all(self):
        """
        Принудительно обновляет весь кэш
        """
        logger.info("Админ запустил принудительное обновление всего кэша")
        results = cache_manager.force_refresh_all(self.fetch_functions)

        message = "🔄 <b>ОБНОВЛЕНИЕ КЭША</b>\n\n"

        success_count = 0
        for data_type, result in results.items():
            if result['status'] == 'success':
                message += f"✅ <b>{data_type}:</b> Успешно обновлено\n"
                success_count += 1
            else:
                message += f"❌ <b>{data_type}:</b> Ошибка - {result['error']}\n"

        message += f"\n📊 Итого: {success_count}/{len(results)} успешно"

        return message

    def force_refresh_specific(self, data_type):
        """
        Принудительно обновляет конкретный тип данных
        """
        if data_type not in self.fetch_functions:
            return f"❌ Неизвестный тип данных: {data_type}"

        logger.info(f"Админ запустил обновление кэша для {data_type}")
        result = cache_manager.force_refresh_specific(data_type, self.fetch_functions[data_type])

        if result['status'] == 'success':
            return f"✅ <b>{data_type}</b> успешно обновлен!\n🕒 Время: {result['data'].get('date', 'N/A')}"
        else:
            return f"❌ Ошибка обновления <b>{data_type}</b>:\n{result['error']}"

    def clear_cache(self, data_type=None):
        """
        Очищает кэш
        """
        logger.info(f"Админ очистил кэш: {data_type or 'весь'}")
        result = cache_manager.clear_cache(data_type)
        return f"🧹 {result}"

# Глобальный экземпляр админ-менеджера
admin_cache_manager = AdminCacheManager()
# smart_cache.py
from datetime import datetime, time
import logging
from config import logger

class SmartCache:
    """
    Умный кэш с расписанием обновления и TTL
    """

    def __init__(self):
        self.cache = {}

        # Расписание обновления для разных типов данных
        self.schedule = {
            'key_rate': ["01:00", "09:30", "11:00", "16:00"],
            'ruonia': ["09:00", "12:00", "15:55", "18:00"],
            'currency': ["11:30", "14:00", "16:30", "23:00"]
        }

        # TTL в часах для каждого типа данных
        self.ttl_hours = {
            'key_rate': 4,    # 4 часа
            'ruonia': 3,      # 3 часа
            'currency': 6     # 6 часов
        }

        logger.info("SmartCache инициализирован")

    def _get_current_time_str(self):
        """Возвращает текущее время в формате HH:MM"""
        return datetime.now().strftime("%H:%M")

    def _time_in_schedule(self, data_type):
        """Проверяет, находится ли текущее время в расписании обновления"""
        current_time = self._get_current_time_str()
        return current_time in self.schedule.get(data_type, [])

    def should_refresh(self, data_type):
        """
        Проверяет, нужно ли обновлять кэш для указанного типа данных
        """
        if data_type not in self.cache:
            logger.debug(f"Кэш для {data_type} пустой - требуется обновление")
            return True

        cache_entry = self.cache[data_type]
        cached_time = cache_entry['timestamp']
        now = datetime.now()

        # Проверка по расписанию
        if self._time_in_schedule(data_type):
            logger.info(f"Время обновления для {data_type} - требуется обновление")
            return True

        # Проверка TTL
        time_diff_hours = (now - cached_time).total_seconds() / 3600
        if time_diff_hours > self.ttl_hours[data_type]:
            logger.info(f"TTL истек для {data_type} ({time_diff_hours:.1f} часов) - требуется обновление")
            return True

        # Кэш еще актуален
        logger.debug(f"Кэш для {data_type} актуален ({time_diff_hours:.1f} часов)")
        return False

    def get_data(self, data_type, fetch_function, force_refresh=False):
        """
        Получает данные из кэша или обновляет их при необходимости

        Args:
            data_type: тип данных ('key_rate', 'ruonia', 'currency')
            fetch_function: функция для получения свежих данных
            force_refresh: принудительное обновление

        Returns:
            Данные из кэша или свежие данные
        """
        try:
            if force_refresh or self.should_refresh(data_type):
                logger.info(f"Обновление кэша для {data_type}")

                # Получаем свежие данные
                fresh_data = fetch_function()

                # Сохраняем в кэш с временной меткой
                self.cache[data_type] = {
                    'data': fresh_data,
                    'timestamp': datetime.now()
                }

                logger.info(f"Кэш для {data_type} успешно обновлен")

            # Возвращаем данные из кэша
            return self.cache[data_type]['data']

        except Exception as e:
            logger.error(f"Ошибка при работе с кэшем для {data_type}: {e}")

            # В случае ошибки пытаемся вернуть старые данные из кэша
            if data_type in self.cache:
                logger.warning(f"Возвращаем устаревшие данные из кэша для {data_type}")
                return self.cache[data_type]['data']

            # Если в кэше ничего нет - пробрасываем исключение
            raise

    def clear_cache(self, data_type=None):
        """
        Очищает кэш для указанного типа данных или весь кэш
        """
        if data_type:
            if data_type in self.cache:
                del self.cache[data_type]
                logger.info(f"Кэш для {data_type} очищен")
        else:
            self.cache.clear()
            logger.info("Весь кэш очищен")

    def get_cache_info(self):
        """
        Возвращает информацию о состоянии кэша
        """
        info = {}
        now = datetime.now()

        for data_type, cache_entry in self.cache.items():
            age_hours = (now - cache_entry['timestamp']).total_seconds() / 3600
            info[data_type] = {
                'age_hours': round(age_hours, 2),
                'timestamp': cache_entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                'needs_refresh': self.should_refresh(data_type)
            }

        return info

# Создаем глобальный экземпляр кэша
cache_manager = SmartCache()
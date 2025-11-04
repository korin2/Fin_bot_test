# smart_cache.py
from datetime import datetime, time
import logging
import pickle
import os
from config import logger

class SmartCache:
    """
    Умный кэш с расписанием обновления, TTL и админ-функциями
    """

    def __init__(self):
        self.cache = {}
        self.cache_file = 'cache_data.pkl'

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

        # Загружаем кэш с диска при старте
        self.load_cache()
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

                # Сохраняем на диск
                self.save_cache()
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

    def load_cache(self):
        """Загружает кэш с диска"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                logger.info(f"Кэш загружен с диска: {len(self.cache)} записей")
            else:
                logger.info("Файл кэша не найден, начинаем с пустого кэша")
        except Exception as e:
            logger.error(f"Ошибка загрузки кэша: {e}")
            self.cache = {}

    def save_cache(self):
        """Сохраняет кэш на диск"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
            logger.debug("Кэш сохранен на диск")
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша: {e}")

    # 🔧 АДМИН-ФУНКЦИИ
    def force_refresh_all(self, fetch_functions):
        """
        Принудительно обновляет все типы данных
        """
        results = {}
        for data_type, fetch_func in fetch_functions.items():
            try:
                logger.info(f"Принудительное обновление кэша для {data_type}")
                fresh_data = fetch_func()
                self.cache[data_type] = {
                    'data': fresh_data,
                    'timestamp': datetime.now()
                }
                results[data_type] = {
                    'status': 'success',
                    'data': fresh_data
                }
                logger.info(f"Кэш для {data_type} успешно обновлен")
            except Exception as e:
                logger.error(f"Ошибка принудительного обновления {data_type}: {e}")
                results[data_type] = {
                    'status': 'error',
                    'error': str(e)
                }

        # Сохраняем обновленный кэш
        self.save_cache()
        return results

    def force_refresh_specific(self, data_type, fetch_function):
        """
        Принудительно обновляет конкретный тип данных
        """
        try:
            logger.info(f"Принудительное обновление кэша для {data_type}")
            fresh_data = fetch_function()
            self.cache[data_type] = {
                'data': fresh_data,
                'timestamp': datetime.now()
            }
            self.save_cache()
            logger.info(f"Кэш для {data_type} успешно обновлен")
            return {'status': 'success', 'data': fresh_data}
        except Exception as e:
            logger.error(f"Ошибка принудительного обновления {data_type}: {e}")
            return {'status': 'error', 'error': str(e)}

    def clear_cache(self, data_type=None):
        """
        Очищает кэш для указанного типа данных или весь кэш
        """
        if data_type:
            if data_type in self.cache:
                del self.cache[data_type]
                self.save_cache()
                logger.info(f"Кэш для {data_type} очищен")
                return f"Кэш для {data_type} очищен"
            else:
                return f"Кэш для {data_type} не найден"
        else:
            self.cache.clear()
            self.save_cache()
            logger.info("Весь кэш очищен")
            return "Весь кэш очищен"

    def get_cache_info(self):
        """
        Возвращает подробную информацию о состоянии кэша
        """
        info = {}
        now = datetime.now()

        for data_type, cache_entry in self.cache.items():
            age_seconds = (now - cache_entry['timestamp']).total_seconds()
            age_hours = age_seconds / 3600
            age_str = f"{int(age_seconds // 3600)}ч {int((age_seconds % 3600) // 60)}м"

            needs_refresh = self.should_refresh(data_type)
            status = "🟢 Актуален" if not needs_refresh else "🟡 Требует обновления"

            info[data_type] = {
                'age_seconds': age_seconds,
                'age_hours': round(age_hours, 2),
                'age_str': age_str,
                'timestamp': cache_entry['timestamp'].strftime("%d.%m.%Y %H:%M:%S"),
                'needs_refresh': needs_refresh,
                'status': status,
                'data_exists': cache_entry['data'] is not None
            }

        return info

# Создаем глобальный экземпляр кэша
cache_manager = SmartCache()
# cache.py
import logging
import time
from datetime import datetime, timedelta
import pytz
from config import logger

# Глобальные переменные для кэша
_cache_data = {}
_cache_timestamps = {}
_cache_ttl = {}
_cache_schedule = {}

def init_cache():
    """Инициализация кэша с настраиваемым расписанием"""
    global _cache_data, _cache_timestamps, _cache_ttl, _cache_schedule
    
    # TTL для разных типов данных (в секундах)
    _cache_ttl = {
        'currency_rates': 3600,      # 1 час
        'key_rate': 86400,           # 24 часа
        'ruonia_rate': 86400,        # 24 часа
        'crypto_rates': 1800,        # 30 минут
        'weather': 1800,             # 30 минут
    }
    
    # 🔄 РАСПИСАНИЕ ОБНОВЛЕНИЯ ПО МОСКОВСКОМУ ВРЕМЕНИ
    _cache_schedule = {
        'currency_rates': ['07:00', '10:00', '13:00', '16:00', '19:00'],  # Курсы валют
        'key_rate': ['08:00'],                                            # Ключевая ставка
        'ruonia_rate': ['08:00'],                                         # RUONIA
        'crypto_rates': ['09:00', '12:00', '15:00', '18:00', '21:00'],    # Криптовалюты
        'weather': ['06:00', '12:00', '18:00']                           # Погода
    }
    
    _cache_data = {}
    _cache_timestamps = {}
    logger.info("✅ Кэш инициализирован с настраиваемым расписанием")

def set_cache(key: str, data, ttl: int = None):
    """Установка данных в кэш"""
    try:
        _cache_data[key] = data
        _cache_timestamps[key] = time.time()
        if ttl:
            _cache_ttl[key] = ttl
        logger.debug(f"✅ Данные добавлены в кэш: {key}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка установки кэша {key}: {e}")
        return False

def get_cache(key: str):
    """Получение данных из кэша с проверкой расписания"""
    try:
        if key not in _cache_data:
            return None
            
        # Проверяем TTL
        if key in _cache_ttl:
            ttl = _cache_ttl[key]
            timestamp = _cache_timestamps.get(key, 0)
            
            # 🔄 ПРОВЕРЯЕМ РАСПИСАНИЕ ОБНОВЛЕНИЯ
            if should_refresh_by_schedule(key):
                logger.info(f"🕒 По расписанию: кэш {key} требует обновления")
                return None
                
            if time.time() - timestamp > ttl:
                logger.debug(f"🕒 Кэш устарел: {key}")
                return None
                
        logger.debug(f"✅ Данные получены из кэша: {key}")
        return _cache_data[key]
    except Exception as e:
        logger.error(f"❌ Ошибка получения кэша {key}: {e}")
        return None

def should_refresh_by_schedule(key: str) -> bool:
    """Проверяет, нужно ли обновить кэш по расписанию"""
    try:
        if key not in _cache_schedule:
            return False
            
        schedule_times = _cache_schedule[key]
        if not schedule_times:
            return False
            
        # Получаем текущее московское время
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time_moscow = datetime.now(moscow_tz)
        current_time_str = current_time_moscow.strftime('%H:%M')
        
        # Получаем время последнего обновления
        last_update_timestamp = _cache_timestamps.get(key, 0)
        if last_update_timestamp == 0:
            return True
            
        last_update_moscow = datetime.fromtimestamp(last_update_timestamp, moscow_tz)
        last_update_str = last_update_moscow.strftime('%H:%M')
        
        # Проверяем, наступило ли время обновления по расписанию
        for schedule_time in schedule_times:
            if current_time_str >= schedule_time and last_update_str < schedule_time:
                logger.info(f"⏰ Сработало расписание: {key} в {schedule_time} МСК")
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки расписания для {key}: {e}")
        return False

def clear_cache(key: str = None):
    """Очистка кэша"""
    try:
        if key:
            _cache_data.pop(key, None)
            _cache_timestamps.pop(key, None)
            logger.info(f"🧹 Кэш очищен: {key}")
        else:
            _cache_data.clear()
            _cache_timestamps.clear()
            logger.info("🧹 Весь кэш очищен")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка очистки кэша: {e}")
        return False

def get_cache_stats():
    """Получение статистики кэша с информацией о расписании"""
    stats = {
        'total_entries': len(_cache_data),
        'entries': {},
        'schedule': _cache_schedule.copy()
    }
    
    for key in _cache_data:
        if key in _cache_timestamps:
            age = time.time() - _cache_timestamps[key]
            ttl = _cache_ttl.get(key, 0)
            remaining_ttl = max(0, ttl - age)
            is_expired = age > ttl if ttl > 0 else False
            
            # Информация о следующем обновлении по расписанию
            next_schedule_time = get_next_schedule_time(key)
            needs_schedule_refresh = should_refresh_by_schedule(key)
            
            stats['entries'][key] = {
                'age_seconds': int(age),
                'age_human': str(timedelta(seconds=int(age))),
                'ttl_seconds': ttl,
                'remaining_ttl': int(remaining_ttl),
                'is_expired': is_expired,
                'data_size': len(str(_cache_data[key])),
                'needs_schedule_refresh': needs_schedule_refresh,
                'next_schedule_time': next_schedule_time,
                'schedule_times': _cache_schedule.get(key, [])
            }
    
    return stats

def get_next_schedule_time(key: str) -> str:
    """Получает следующее время обновления по расписанию"""
    try:
        if key not in _cache_schedule:
            return "не настроено"
            
        schedule_times = _cache_schedule[key]
        if not schedule_times:
            return "не настроено"
            
        # Получаем текущее московское время
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time_moscow = datetime.now(moscow_tz)
        current_time_str = current_time_moscow.strftime('%H:%M')
        
        # Ищем следующее время в расписании
        for schedule_time in sorted(schedule_times):
            if schedule_time > current_time_str:
                return f"{schedule_time} МСК"
                
        # Если все времена прошли, берем первое на завтра
        return f"{sorted(schedule_times)[0]} МСК (завтра)"
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения следующего времени для {key}: {e}")
        return "ошибка"

def update_cache_schedule(key: str, times: list):
    """Обновляет расписание обновления для конкретного типа данных"""
    try:
        _cache_schedule[key] = times
        logger.info(f"✅ Расписание обновлено для {key}: {times}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка обновления расписания для {key}: {e}")
        return False

def get_cache_schedule():
    """Возвращает текущее расписание"""
    return _cache_schedule.copy()

def force_refresh_cache(key: str = None):
    """Принудительное обновление кэша"""
    try:
        if key:
            clear_cache(key)
            logger.info(f"🔄 Принудительное обновление кэша: {key}")
        else:
            clear_cache()
            logger.info("🔄 Принудительное обновление всего кэша")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка принудительного обновления кэша: {e}")
        return False

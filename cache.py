# cache.py
import logging
import time
from datetime import datetime, timedelta
from config import logger

# Глобальные переменные для кэша
_cache_data = {}
_cache_timestamps = {}
_cache_ttl = {}

def init_cache():
    """Инициализация кэша"""
    global _cache_data, _cache_timestamps, _cache_ttl
    
    # TTL для разных типов данных (в секундах)
    _cache_ttl = {
        'currency_rates': 3600,      # 1 час
        'key_rate': 86400,           # 24 часа
        'ruonia_rate': 86400,        # 24 часа
        'crypto_rates': 1800,        # 30 минут
        'weather': 1800,             # 30 минут
    }
    
    _cache_data = {}
    _cache_timestamps = {}
    logger.info("✅ Кэш инициализирован")

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
    """Получение данных из кэша"""
    try:
        if key not in _cache_data:
            return None
            
        # Проверяем TTL
        if key in _cache_ttl:
            ttl = _cache_ttl[key]
            timestamp = _cache_timestamps.get(key, 0)
            if time.time() - timestamp > ttl:
                logger.debug(f"🕒 Кэш устарел: {key}")
                return None
                
        logger.debug(f"✅ Данные получены из кэша: {key}")
        return _cache_data[key]
    except Exception as e:
        logger.error(f"❌ Ошибка получения кэша {key}: {e}")
        return None

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
    """Получение статистики кэша"""
    stats = {
        'total_entries': len(_cache_data),
        'entries': {}
    }
    
    for key in _cache_data:
        if key in _cache_timestamps:
            age = time.time() - _cache_timestamps[key]
            ttl = _cache_ttl.get(key, 0)
            remaining_ttl = max(0, ttl - age)
            is_expired = age > ttl if ttl > 0 else False
            
            stats['entries'][key] = {
                'age_seconds': int(age),
                'age_human': str(timedelta(seconds=int(age))),
                'ttl_seconds': ttl,
                'remaining_ttl': int(remaining_ttl),
                'is_expired': is_expired,
                'data_size': len(str(_cache_data[key]))
            }
    
    return stats

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

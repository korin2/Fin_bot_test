# api_crypto.py - полностью обновляем для работы с кэшированием
import requests
import json
from datetime import datetime, timezone, timedelta
import logging
from config import logger, COINGECKO_API_BASE, COINGECKO_API_KEY

# 🔄 ДОБАВЛЯЕМ ИМПОРТ ДЛЯ КЭШИРОВАНИЯ
from cache import get_cache, set_cache

def get_crypto_rates():
    """Получает курсы криптовалют через CoinGecko API с использованием API ключа И КЭШИРОВАНИЯ"""
    try:
        # 🎯 ПРОВЕРЯЕМ КЭШ ПЕРВЫМ ДЕЛОМ
        cache_key = "crypto_rates"
        cached_data = get_cache(cache_key)

        # ✅ ЕСЛИ ДАННЫЕ ЕСТЬ В КЭШЕ - ВОЗВРАЩАЕМ ИХ
        if cached_data:
            logger.info("💾 Используются кэшированные данные криптовалют")
            return cached_data

        # 🔄 ЕСЛИ ДАННЫХ НЕТ В КЭШЕ - ЗАПРАШИВАЕМ У API
        logger.info("🌐 Запрашиваем свежие данные криптовалют у CoinGecko API")

        # Основные криптовалюты для отслеживания
        crypto_ids = [
            'bitcoin', 'ethereum', 'binancecoin', 'ripple', 'cardano',
            'solana', 'polkadot', 'dogecoin', 'tron', 'litecoin'
        ]

        url = f"{COINGECKO_API_BASE}/simple/price"
        params = {
            'ids': ','.join(crypto_ids),
            'vs_currencies': 'rub,usd',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true',
            'precision': 'full'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

        # Добавляем API ключ если он есть
        if COINGECKO_API_KEY:
            headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
            logger.info("Используется API ключ CoinGecko")
        else:
            logger.info("API ключ CoinGecko не найден, используем бесплатные запросы")

        logger.info(f"Запрос к CoinGecko API: {url}")
        logger.info(f"Параметры: {params}")

        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code == 429:
            logger.warning("Превышен лимит запросов к CoinGecko API (429)")
            return get_crypto_rates_fallback(rate_limit=True)
        elif response.status_code == 401:
            logger.error("Неверный API ключ CoinGecko (401)")
            return get_crypto_rates_fallback(auth_error=True)
        elif response.status_code != 200:
            logger.error(f"Ошибка CoinGecko API: {response.status_code}")
            logger.error(f"Текст ответа: {response.text}")
            return get_crypto_rates_fallback()

        data = response.json()
        logger.info(f"Успешно получены данные от CoinGecko: {len(data)} криптовалют")

        # Проверяем структуру ответа
        if not isinstance(data, dict):
            logger.error(f"Неправильный формат ответа: ожидался dict, получен {type(data)}")
            return get_crypto_rates_fallback()

        # Маппинг названий криптовалют
        crypto_names = {
            'bitcoin': {'name': 'Bitcoin', 'symbol': 'BTC'},
            'ethereum': {'name': 'Ethereum', 'symbol': 'ETH'},
            'binancecoin': {'name': 'Binance Coin', 'symbol': 'BNB'},
            'ripple': {'name': 'XRP', 'symbol': 'XRP'},
            'cardano': {'name': 'Cardano', 'symbol': 'ADA'},
            'solana': {'name': 'Solana', 'symbol': 'SOL'},
            'polkadot': {'name': 'Polkadot', 'symbol': 'DOT'},
            'dogecoin': {'name': 'Dogecoin', 'symbol': 'DOGE'},
            'tron': {'name': 'TRON', 'symbol': 'TRX'},
            'litecoin': {'name': 'Litecoin', 'symbol': 'LTC'}
        }

        crypto_rates = {}
        valid_count = 0

        for crypto_id, info in crypto_names.items():
            if crypto_id in data:
                crypto_data = data[crypto_id]

                # Проверяем что crypto_data - словарь
                if not isinstance(crypto_data, dict):
                    logger.warning(f"Данные для {crypto_id} не словарь: {type(crypto_data)}")
                    continue

                # Получаем цены с проверкой
                price_rub = crypto_data.get('rub')
                price_usd = crypto_data.get('usd')

                # Получаем изменение цены (может быть под разными ключами)
                change_24h = crypto_data.get('rub_24h_change') or crypto_data.get('usd_24h_change') or 0

                # Проверяем что цены есть и они числа
                if price_rub is None or price_usd is None:
                    logger.warning(f"Отсутствуют цены для {crypto_id}: RUB={price_rub}, USD={price_usd}")
                    continue

                try:
                    price_rub = float(price_rub)
                    price_usd = float(price_usd)
                    change_24h = float(change_24h) if change_24h is not None else 0
                except (TypeError, ValueError) as e:
                    logger.warning(f"Ошибка преобразования данных для {crypto_id}: {e}")
                    continue

                crypto_rates[crypto_id] = {
                    'name': info['name'],
                    'symbol': info['symbol'],
                    'price_rub': price_rub,
                    'price_usd': price_usd,
                    'change_24h': change_24h,
                    'last_updated': crypto_data.get('last_updated_at', 0)
                }
                valid_count += 1

        logger.info(f"Успешно обработано {valid_count} криптовалют")

        if crypto_rates:
            # Исправляем время на московское (UTC+3)
            moscow_tz = timezone(timedelta(hours=3))
            crypto_rates['update_time'] = datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M')
            crypto_rates['source'] = 'coingecko'
            crypto_rates['rate_limit'] = False
            crypto_rates['auth_error'] = False
            crypto_rates['api_key_used'] = bool(COINGECKO_API_KEY)

            # 💾 СОХРАНЯЕМ РЕЗУЛЬТАТ В КЭШ
            set_cache(cache_key, crypto_rates)
            logger.info("💾 Данные криптовалют сохранены в кэш на 30 минут")

            return crypto_rates
        else:
            logger.error("Не найдено валидных данных по криптовалютам в ответе API")
            return get_crypto_rates_fallback()

    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к CoinGecko API")
        return get_crypto_rates_fallback()
    except requests.exceptions.RequestException as e:
        logger.error(f"Сетевая ошибка при получении курсов криптовалют: {e}")
        return get_crypto_rates_fallback()
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON от CoinGecko: {e}")
        return get_crypto_rates_fallback()
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении курсов криптовалют: {e}")
        return get_crypto_rates_fallback()

def get_crypto_rates_fallback(rate_limit=False, auth_error=False):
    """Резервная функция для получения курсов криптовалют (демо-данные) С КЭШИРОВАНИЕМ"""
    try:
        # 🎯 ПРОВЕРЯЕМ КЭШ ДЛЯ FALLBACK ДАННЫХ
        cache_key = "crypto_rates_fallback"
        cached_data = get_cache(cache_key)

        if cached_data:
            logger.info("💾 Используются кэшированные демо-данные криптовалют")
            return cached_data

        # 🔄 ЕСЛИ ДАННЫХ НЕТ В КЭШЕ - СОЗДАЕМ ДЕМО-ДАННЫЕ
        logger.info("🔄 Используем демо-данные криптовалют")

        # Демо-данные на случай недоступности API
        crypto_rates = {
            'bitcoin': {
                'name': 'Bitcoin',
                'symbol': 'BTC',
                'price_rub': 4500000.0,
                'price_usd': 50000.0,
                'change_24h': 2.5,
                'last_updated': datetime.now().timestamp()
            },
            'ethereum': {
                'name': 'Ethereum',
                'symbol': 'ETH',
                'price_rub': 300000.0,
                'price_usd': 3300.0,
                'change_24h': 1.2,
                'last_updated': datetime.now().timestamp()
            },
            'binancecoin': {
                'name': 'Binance Coin',
                'symbol': 'BNB',
                'price_rub': 35000.0,
                'price_usd': 380.0,
                'change_24h': -0.5,
                'last_updated': datetime.now().timestamp()
            },
            'ripple': {
                'name': 'XRP',
                'symbol': 'XRP',
                'price_rub': 60.0,
                'price_usd': 0.65,
                'change_24h': 0.8,
                'last_updated': datetime.now().timestamp()
            },
            'cardano': {
                'name': 'Cardano',
                'symbol': 'ADA',
                'price_rub': 45.0,
                'price_usd': 0.48,
                'change_24h': -1.2,
                'last_updated': datetime.now().timestamp()
            },
            'solana': {
                'name': 'Solana',
                'symbol': 'SOL',
                'price_rub': 15000.0,
                'price_usd': 160.0,
                'change_24h': 3.2,
                'last_updated': datetime.now().timestamp()
            },
            'polkadot': {
                'name': 'Polkadot',
                'symbol': 'DOT',
                'price_rub': 800.0,
                'price_usd': 8.5,
                'change_24h': 1.5,
                'last_updated': datetime.now().timestamp()
            },
            'dogecoin': {
                'name': 'Dogecoin',
                'symbol': 'DOGE',
                'price_rub': 30.0,
                'price_usd': 0.32,
                'change_24h': -2.1,
                'last_updated': datetime.now().timestamp()
            }
        }

        moscow_tz = timezone(timedelta(hours=3))
        crypto_rates['update_time'] = datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M')
        crypto_rates['source'] = 'demo_fallback'
        crypto_rates['rate_limit'] = rate_limit
        crypto_rates['auth_error'] = auth_error
        crypto_rates['api_key_used'] = False

        # 💾 СОХРАНЯЕМ FALLBACK ДАННЫЕ В КЭШ
        set_cache(cache_key, crypto_rates)
        logger.info("💾 Демо-данные криптовалют сохранены в кэш на 30 минут")

        return crypto_rates

    except Exception as e:
        logger.error(f"Ошибка в fallback функции криптовалют: {e}")
        return None

def format_crypto_rates_message(crypto_rates: dict) -> str:
    """Форматирует сообщение с курсами криптовалют"""
    if not crypto_rates:
        return "❌ Не удалось получить курсы криптовалют от CoinGecko API."

    message = f"₿ <b>КУРСЫ КРИПТОВАЛЮТ</b>\n\n"

    # Добавляем информацию о статусе API
    if crypto_rates.get('source') == 'demo_fallback':
        if crypto_rates.get('auth_error'):
            message += "🔐 <b>ВНИМАНИЕ:</b> Ошибка аутентификации CoinGecko API\n"
            message += "💡 <i>Используются демонстрационные данные</i>\n\n"
        elif crypto_rates.get('rate_limit'):
            message += "⚠️ <b>ВНИМАНИЕ:</b> Превышен лимит запросов к CoinGecko API\n"
            message += "💡 <i>Используются демонстрационные данные</i>\n\n"
        else:
            message += "⚠️ <b>ВНИМАНИЕ:</b> CoinGecko API временно недоступен\n"
            message += "💡 <i>Используются демонстрационные данные</i>\n\n"
    else:
        # Показываем статус API ключа при успешном запросе
        if crypto_rates.get('api_key_used'):
            message += "🔐 <b>Статус:</b> Используется API ключ CoinGecko\n\n"
        else:
            message += "🆓 <b>Статус:</b> Бесплатный тариф CoinGecko\n\n"

    # Основные криптовалюты (первые 5)
    main_cryptos = ['bitcoin', 'ethereum', 'binancecoin', 'ripple', 'cardano']

    for crypto_id in main_cryptos:
        if crypto_id in crypto_rates:
            data = crypto_rates[crypto_id]

            # Безопасное получение данных
            name = data.get('name', 'N/A')
            symbol = data.get('symbol', 'N/A')
            price_rub = data.get('price_rub', 0)
            price_usd = data.get('price_usd', 0)
            change_24h = data.get('change_24h', 0)

            # Проверяем типы данных
            try:
                price_rub = float(price_rub)
                price_usd = float(price_usd)
                change_24h = float(change_24h)
            except (TypeError, ValueError):
                continue

            change_icon = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"

            message += (
                f"<b>{name} ({symbol})</b>\n"
                f"   💰 <b>{price_rub:,.0f} руб.</b>\n"
                f"   💵 {price_usd:,.2f} $\n"
                f"   {change_icon} <i>{change_24h:+.2f}% (24ч)</i>\n\n"
            )

    # Остальные криптовалюты
    other_cryptos = [crypto_id for crypto_id in crypto_rates.keys()
                    if crypto_id not in main_cryptos and crypto_id not in ['update_time', 'source', 'rate_limit', 'auth_error', 'api_key_used']]

    if other_cryptos:
        message += "🔹 <b>Другие криптовалюты:</b>\n"

        for crypto_id in other_cryptos:
            data = crypto_rates[crypto_id]
            symbol = data.get('symbol', 'N/A')
            price_rub = data.get('price_rub', 0)
            change_24h = data.get('change_24h', 0)

            try:
                price_rub = float(price_rub)
                change_24h = float(change_24h)
            except (TypeError, ValueError):
                continue

            change_icon = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"

            message += (
                f"   <b>{symbol}</b>: {price_rub:,.0f} руб. {change_icon}\n"
            )

    message += f"\n<i>Обновлено: {crypto_rates.get('update_time', 'неизвестно')} (МСК)</i>\n\n"

    if crypto_rates.get('source') == 'coingecko':
        if crypto_rates.get('api_key_used'):
            message += "💡 <i>Данные предоставлены CoinGecko API (премиум)</i>"
        else:
            message += "💡 <i>Данные предоставлены CoinGecko API (бесплатный тариф)</i>"
    else:
        message += "💡 <i>Данные обновятся при восстановлении доступа к CoinGecko API</i>"

    # 🔄 ДОБАВЛЯЕМ ИНФОРМАЦИЮ О КЭШИРОВАНИИ
    message += f"\n\n💾 <i>Данные обновляются каждые 30 минут</i>"

    return message

# 🔧 ДОБАВЛЯЕМ ФУНКЦИЮ ПРИНУДИТЕЛЬНОГО ОБНОВЛЕНИЯ
def refresh_crypto_cache():
    """Принудительно обновляет кэш криптовалют"""
    try:
        from cache import force_refresh_cache

        # Очищаем кэш для криптовалют
        force_refresh_cache("crypto_rates")
        force_refresh_cache("crypto_rates_fallback")

        logger.info("🔄 Кэш криптовалют принудительно обновлен")
        return True

    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша криптовалют: {e}")
        return False
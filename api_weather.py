import requests
import random
from datetime import datetime, timezone, timedelta
import logging
from config import OPENWEATHER_API_BASE, WEATHER_API_KEY, logger

def get_weather_moscow():
    """Получает текущую погоду в Москве через OpenWeatherMap API"""
    try:
        # Если API ключ не установлен, используем демо-данные
        if not WEATHER_API_KEY or WEATHER_API_KEY == 'demo_key_12345':
            logger.warning("API ключ погоды не настроен, используем демо-данные")
            return get_weather_demo()
        
        CITY = "Moscow"
        URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        
        logger.info(f"Запрос погоды для города: {CITY}")
        response = requests.get(URL, timeout=10)
        
        if response.status_code == 401:
            logger.error("Невалидный API ключ OpenWeatherMap")
            return get_weather_demo()
        elif response.status_code == 429:
            logger.error("Превышен лимит запросов к API погоды")
            return get_weather_demo()
        elif response.status_code != 200:
            logger.error(f"Ошибка API погоды: {response.status_code} - {response.text}")
            return get_weather_demo()
            
        data = response.json()
        
        weather_info = {
            'city': data['name'],
            'temperature': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'description': data['weather'][0]['description'].capitalize(),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'icon': data['weather'][0]['icon'],
            'source': 'openweathermap'
        }
        
        logger.info(f"Погода получена: {weather_info['temperature']}°C, {weather_info['description']}")
        return weather_info
        
    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе погоды")
        return get_weather_demo()
    except requests.exceptions.RequestException as e:
        logger.error(f"Сетевая ошибка при получении погоды: {e}")
        return get_weather_demo()
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении погоды: {e}")
        return get_weather_demo()

def get_weather_demo():
    """Демо-данные погоды на случай недоступности API"""
    # Сезонные температуры для реалистичности
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:  # Зима
        temp_range = (-15, -2)
    elif current_month in [3, 4, 5]:  # Весна
        temp_range = (0, 15)
    elif current_month in [6, 7, 8]:  # Лето
        temp_range = (15, 30)
    else:  # Осень
        temp_range = (5, 18)
    
    descriptions = [
        "ясно", "переменная облачность", "облачно с прояснениями", 
        "небольшой дождь", "пасмурно", "снег", "небольшая облачность"
    ]
    
    weather_data = {
        'city': 'Москва',
        'temperature': random.randint(temp_range[0], temp_range[1]),
        'feels_like': 0,
        'description': random.choice(descriptions),
        'humidity': random.randint(40, 90),
        'pressure': random.randint(740, 780),
        'wind_speed': round(random.uniform(1, 8), 1),
        'icon': '02d',
        'source': 'demo'
    }
    
    # Делаем "ощущается как" реалистичным
    weather_data['feels_like'] = weather_data['temperature'] + random.randint(-3, 2)
    
    return weather_data

def format_weather_message(weather_data):
    """Форматирует сообщение с погодой"""
    if not weather_data:
        return "❌ Не удалось получить данные о погоде."
    
    # Эмодзи для разных типов погоды
    weather_emojis = {
        'ясно': '☀️',
        'переменная облачность': '⛅',
        'облачно с прояснениями': '🌤️',
        'небольшой дождь': '🌦️',
        'пасмурно': '☁️',
        'снег': '❄️',
        'небольшая облачность': '🌤️'
    }
    
    description_lower = weather_data['description'].lower()
    emoji = '🌡️'
    for key, value in weather_emojis.items():
        if key in description_lower:
            emoji = value
            break
    
    message = (
        f"{emoji} <b>ПОГОДА В {weather_data['city'].upper()}</b>\n\n"
        f"🌡️ <b>Температура:</b> {weather_data['temperature']}°C\n"
        f"🤔 <b>Ощущается как:</b> {weather_data['feels_like']}°C\n"
        f"📝 <b>Описание:</b> {weather_data['description']}\n"
        f"💧 <b>Влажность:</b> {weather_data['humidity']}%\n"
        f"📊 <b>Давление:</b> {weather_data['pressure']} мм рт.ст.\n"
        f"💨 <b>Ветер:</b> {weather_data['wind_speed']} м/с\n\n"
    )
    
    # Добавляем рекомендации по одежде
    temp = weather_data['temperature']
    if temp >= 20:
        recommendation = "👕 Легкая одежда, можно в футболке"
    elif temp >= 15:
        recommendation = "👚 Длинный рукав или легкая кофта"
    elif temp >= 10:
        recommendation = "🧥 Легкая куртка или кофта"
    elif temp >= 0:
        recommendation = "🧥 Теплая куртка, шапка"
    else:
        recommendation = "🧣 Зимняя куртка, шапка, шарф, перчатки"
    
    message += f"👗 <b>Рекомендация:</b> {recommendation}\n\n"
    
    if weather_data['source'] == 'demo':
        message += "⚠️ <i>Используются демонстрационные данные (API ключ не настроен или недоступен)</i>\n"
        message += "💡 <i>Для реальных данных настройте API ключ OpenWeatherMap</i>\n"
    else:
        message += "✅ <i>Актуальные данные от OpenWeatherMap</i>\n"
    
    # Исправляем время на московское (UTC+3)
    moscow_tz = timezone(timedelta(hours=3))
    message += f"🕒 <i>Обновлено: {datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M')} (МСК)</i>"
    
    return message

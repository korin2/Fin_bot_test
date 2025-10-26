
import requests
import time
import sys
from config import TOKEN

def check_bot_health():
    """Проверяет, запущен ли бот и отвечает ли он"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Бот активен и отвечает")
            return True
        else:
            print(f"❌ Бот не отвечает. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки здоровья бота: {e}")
        return False

if __name__ == "__main__":
    if check_bot_health():
        sys.exit(0)
    else:
        sys.exit(1)

import os
import logging
from telegram.ext import Application

logger = logging.getLogger(__name__)

def setup_railway_webhook(application: Application, token: str):
    """Настройка Webhook для Railway"""
    try:
        # Получаем URL приложения от Railway
        railway_url = os.getenv('RAILWAY_STATIC_URL')
        if not railway_url:
            # Если нет статического URL, используем общий
            railway_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        
        if railway_url:
            webhook_url = f"https://{railway_url}/{token}"
            logger.info(f"Setting webhook to: {webhook_url}")
            
            # Устанавливаем webhook
            application.run_webhook(
                listen="0.0.0.0",
                port=int(os.getenv('PORT', 8000)),
                url_path=token,
                webhook_url=webhook_url
            )
            return True
        else:
            logger.warning("Railway URL not found, using polling")
            return False
            
    except Exception as e:
        logger.error(f"Webhook setup failed: {e}")
        return False

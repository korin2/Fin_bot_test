import logging
from telegram.ext import ContextTypes
from datetime import datetime
from config import logger
# Обновляем импорты
from notifications import check_alerts, send_daily_rates, send_daily_weather

def setup_jobs(application):
    """Настройка фоновых задач"""
    try:
        job_queue = application.job_queue

        if job_queue:
            logger.info("🔧 JobQueue доступен, настраиваем задачи...")

            # Ежедневная рассылка курсов валют в 15:00 (12:00 UTC)
            job_queue.run_daily(
                send_daily_rates,
                time=datetime.strptime("14:30", "%H:%M").time(),
                days=(0, 1, 2, 3, 4, 5, 6),
                name="daily_rates"
            )

            # Ежедневная рассылка погоды в 10:00 (07:00 UTC)
            job_queue.run_daily(
                send_daily_weather,
                time=datetime.strptime("07:00", "%H:%M").time(),
                days=(0, 1, 2, 3, 4, 5, 6),
                name="daily_weather"
            )

            # Проверка уведомлений каждые 30 минут
            job_queue.run_repeating(check_alerts, interval=1800, first=10, name="check_alerts")

            logger.info("✅ Фоновые задачи настроены")
            logger.info("   📅 Ежедневная рассылка курсов: 15:00 МСК (12:00 UTC)")
            logger.info("   🌤️ Ежедневная рассылка погоды: 10:00 МСК (07:00 UTC)")
            logger.info("   🔔 Проверка уведомлений: каждые 30 минут")

        else:
            logger.warning("❌ JobQueue не доступен - фоновые задачи отключены")

    except Exception as e:
        logger.error(f"Ошибка при настройке фоновых задач: {e}")

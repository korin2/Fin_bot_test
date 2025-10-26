from aiohttp import web
import logging

logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint для Railway"""
    return web.json_response({
        "status": "healthy",
        "service": "telegram-bot",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

def setup_health_check():
    """Настройка health check сервера"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    return app

async def start_health_server():
    """Запуск health check сервера"""
    app = setup_health_check()
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Используем порт от Railway или 8000 по умолчанию
    port = int(__import__('os').getenv('PORT', 8000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Health check server started on port {port}")
    return runner

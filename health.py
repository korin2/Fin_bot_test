"""
Health check endpoints for Railway deployment
"""
from aiohttp import web
import logging
import os
import asyncpg

logger = logging.getLogger(__name__)

async def health_check(request):
    """Basic health check endpoint"""
    try:
        # Проверка подключения к базе данных
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            conn = await asyncpg.connect(database_url)
            await conn.close()
            db_status = "✅ Connected"
        else:
            db_status = "⚠️ Not configured"
        
        return web.json_response({
            "status": "healthy",
            "service": "telegram-finance-bot",
            "database": db_status,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "version": "1.0.0"
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }, status=500)

async def readiness_check(request):
    """Readiness check for Railway"""
    return web.json_response({
        "status": "ready",
        "service": "telegram-finance-bot"
    })

def create_health_app():
    """Create health check application"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/ready', readiness_check)
    app.router.add_get('/', health_check)  # Root also returns health
    return app

async def start_health_server(port=8000):
    """Start health check server (for separate process)"""
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', port))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Health check server started on port {port}")
    return runner

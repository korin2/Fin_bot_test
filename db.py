import asyncpg
import os
from contextlib import asynccontextmanager
import logging
from config import logger

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("Требуется переменная окружения DATABASE_URL")

async def init_db():
    """Инициализация базы данных и создание таблиц"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Создаем таблицу users
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Создаем таблицу alerts
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                threshold DECIMAL NOT NULL,
                direction TEXT NOT NULL CHECK (direction IN ('above', 'below')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')

        # Проверяем существование колонки is_active и добавляем если нет
        try:
            # Проверяем существование колонки
            result = await conn.fetchval('''
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='alerts' AND column_name='is_active'
            ''')

            if result is None:
                # Добавляем колонку is_active если её нет
                await conn.execute('ALTER TABLE alerts ADD COLUMN is_active BOOLEAN DEFAULT TRUE')
                print("Колонка is_active добавлена в таблицу alerts")
            else:
                print("Колонка is_active уже существует")

        except Exception as e:
            print(f"Ошибка при проверке/добавлении колонки is_active: {e}")
            # Если не удалось проверить, просто продолжаем

        await conn.close()
        print("Таблицы созданы успешно")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        raise

        # В db.py добавляем новую таблицу
async def init_db():
    """Инициализация базы данных и создание таблиц"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Существующие таблицы...

        # Создаем таблицу user_actions для статистики использования
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                action_type TEXT NOT NULL,
                action_name TEXT NOT NULL,
                details JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')

        # Создаем индекс для быстрого поиска по пользователю и действию
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id);
        ''')

        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_actions_action_type ON user_actions(action_type);
        ''')

        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_actions_created_at ON user_actions(created_at);
        ''')

        await conn.close()
        print("✅ Таблицы созданы успешно")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        raise

# Добавляем функции для работы со статистикой
async def log_user_action(user_id: int, action_type: str, action_name: str, details: dict = None):
    """Логирует действие пользователя в базу данных"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('''
            INSERT INTO user_actions (user_id, action_type, action_name, details)
            VALUES ($1, $2, $3, $4)
        ''', user_id, action_type, action_name, details)
        await conn.close()
    except Exception as e:
        print(f"Ошибка при логировании действия пользователя: {e}")

async def get_user_actions_stats(days: int = 30):
    """Получает статистику действий пользователей за указанное количество дней"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Общая статистика по действиям
        total_stats = await conn.fetchrow('''
            SELECT
                COUNT(*) as total_actions,
                COUNT(DISTINCT user_id) as unique_users,
                MIN(created_at) as first_action,
                MAX(created_at) as last_action
            FROM user_actions
            WHERE created_at >= NOW() - INTERVAL '$1 days'
        ''', days)

        # Статистика по типам действий
        action_type_stats = await conn.fetch('''
            SELECT
                action_type,
                COUNT(*) as action_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_actions
            WHERE created_at >= NOW() - INTERVAL '$1 days'
            GROUP BY action_type
            ORDER BY action_count DESC
        ''', days)

        # Самые популярные действия
        popular_actions = await conn.fetch('''
            SELECT
                action_name,
                COUNT(*) as action_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_actions
            WHERE created_at >= NOW() - INTERVAL '$1 days'
            GROUP BY action_name
            ORDER BY action_count DESC
            LIMIT 15
        ''', days)

        # Активность по дням
        daily_activity = await conn.fetch('''
            SELECT
                DATE(created_at) as action_date,
                COUNT(*) as action_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_actions
            WHERE created_at >= NOW() - INTERVAL '$1 days'
            GROUP BY DATE(created_at)
            ORDER BY action_date DESC
            LIMIT 30
        ''', days)

        # Самые активные пользователи
        active_users = await conn.fetch('''
            SELECT
                user_id,
                COUNT(*) as action_count,
                MIN(created_at) as first_action,
                MAX(created_at) as last_action
            FROM user_actions
            WHERE created_at >= NOW() - INTERVAL '$1 days'
            GROUP BY user_id
            ORDER BY action_count DESC
            LIMIT 10
        ''', days)

        await conn.close()

        return {
            'total_stats': dict(total_stats) if total_stats else {},
            'action_type_stats': [dict(row) for row in action_type_stats],
            'popular_actions': [dict(row) for row in popular_actions],
            'daily_activity': [dict(row) for row in daily_activity],
            'active_users': [dict(row) for row in active_users]
        }

    except Exception as e:
        print(f"Ошибка при получении статистики действий: {e}")
        return {}

async def get_user_detailed_stats(user_id: int, days: int = 30):
    """Получает детальную статистику по конкретному пользователю"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Общая статистика пользователя
        user_stats = await conn.fetchrow('''
            SELECT
                COUNT(*) as total_actions,
                MIN(created_at) as first_action,
                MAX(created_at) as last_action,
                COUNT(DISTINCT action_type) as unique_action_types,
                COUNT(DISTINCT action_name) as unique_actions
            FROM user_actions
            WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '$2 days'
        ''', user_id, days)

        # Действия по типам
        user_actions_by_type = await conn.fetch('''
            SELECT
                action_type,
                COUNT(*) as action_count,
                MIN(created_at) as first_action,
                MAX(created_at) as last_action
            FROM user_actions
            WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '$2 days'
            GROUP BY action_type
            ORDER BY action_count DESC
        ''', user_id, days)

        # Последние действия
        recent_actions = await conn.fetch('''
            SELECT
                action_type,
                action_name,
                details,
                created_at
            FROM user_actions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 20
        ''', user_id)

        await conn.close()

        return {
            'user_stats': dict(user_stats) if user_stats else {},
            'user_actions_by_type': [dict(row) for row in user_actions_by_type],
            'recent_actions': [dict(row) for row in recent_actions]
        }

    except Exception as e:
        print(f"Ошибка при получении детальной статистики пользователя: {e}")
        return {}

async def get_user_info(user_id: int):
    """Получает информацию о пользователе"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        user = await conn.fetchrow('''
            SELECT user_id, first_name, username, created_at
            FROM users
            WHERE user_id = $1
        ''', user_id)
        await conn.close()
        return dict(user) if user else None
    except Exception as e:
        print(f"Ошибка при получении информации о пользователе: {e}")
        return None


async def update_user_info(user_id: int, first_name: str, username: str = None):
    """Обновление информации о пользователе"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('''
            INSERT INTO users (user_id, first_name, username)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET first_name = $2, username = $3
        ''', user_id, first_name, username)
        await conn.close()
    except Exception as e:
        print(f"Ошибка при обновлении информации о пользователе: {e}")
        raise

async def add_alert(user_id: int, from_curr: str, to_curr: str, threshold: float, direction: str):
    """Добавление уведомления"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('''
            INSERT INTO alerts (user_id, from_currency, to_currency, threshold, direction)
            VALUES ($1, $2, $3, $4, $5)
        ''', user_id, from_curr, to_curr, threshold, direction)
        await conn.close()
    except Exception as e:
        print(f"Ошибка при добавлении уведомления: {e}")
        raise

async def get_all_users():
    """Получение всех пользователей"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        users = await conn.fetch('SELECT user_id FROM users')
        await conn.close()
        return users
    except Exception as e:
        print(f"Ошибка при получении пользователей: {e}")
        return []

async def get_all_alerts():
    """Получение всех уведомлений"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        alerts = await conn.fetch('SELECT * FROM alerts')
        await conn.close()
        return alerts
    except Exception as e:
        print(f"Ошибка при получении уведомлений: {e}")
        return []

async def get_user_alerts(user_id: int):
    """Получение уведомлений пользователя"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Сначала проверяем существование колонки is_active
        try:
            alerts = await conn.fetch(
                'SELECT * FROM alerts WHERE user_id = $1 AND is_active = TRUE ORDER BY created_at DESC',
                user_id
            )
        except asyncpg.exceptions.UndefinedColumnError:
            # Если колонки is_active нет, получаем все активные уведомления
            alerts = await conn.fetch(
                'SELECT * FROM alerts WHERE user_id = $1 ORDER BY created_at DESC',
                user_id
            )

        await conn.close()
        return alerts
    except Exception as e:
        print(f"Ошибка при получении уведомлений пользователя: {e}")
        return []

async def remove_alert(alert_id: int):
    """Удаление уведомления"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('DELETE FROM alerts WHERE id = $1', alert_id)
        await conn.close()
    except Exception as e:
        print(f"Ошибка при удалении уведомления: {e}")
        raise

async def deactivate_alert(alert_id: int):
    """Деактивация уведомления (помечаем как неактивное)"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Сначала проверяем существование колонки is_active
        try:
            await conn.execute('UPDATE alerts SET is_active = FALSE WHERE id = $1', alert_id)
        except asyncpg.exceptions.UndefinedColumnError:
            # Если колонки is_active нет, удаляем уведомление
            await conn.execute('DELETE FROM alerts WHERE id = $1', alert_id)

        await conn.close()
    except Exception as e:
        print(f"Ошибка при деактивации уведомления: {e}")
        raise

async def get_all_active_alerts():
    """Получение всех активных уведомлений"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Сначала проверяем существование колонки is_active
        try:
            alerts = await conn.fetch('SELECT * FROM alerts WHERE is_active = TRUE')
        except asyncpg.exceptions.UndefinedColumnError:
            # Если колонки is_active нет, получаем все уведомления
            alerts = await conn.fetch('SELECT * FROM alerts')

        await conn.close()
        return alerts
    except Exception as e:
        print(f"Ошибка при получении всех уведомлений: {e}")
        return []

async def clear_user_alerts(user_id: int):
    """Очистка всех уведомлений пользователя"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('DELETE FROM alerts WHERE user_id = $1', user_id)
        await conn.close()
    except Exception as e:
        print(f"Ошибка при очистке уведомлений пользователя: {e}")
        raise
@asynccontextmanager
async def get_connection():
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            await conn.close()

# Использование:
async def get_user_alerts(user_id: int):
    async with get_connection() as conn:
        return await conn.fetch(
            'SELECT * FROM alerts WHERE user_id = $1 AND is_active = TRUE',
            user_id
        )

# db.py - добавляем новую таблицу
async def init_db():
    """Инициализация базы данных и создание таблиц"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Существующие таблицы...

        # Создаем таблицу user_settings для хранения настроек
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id BIGINT PRIMARY KEY,
                weather_notifications BOOLEAN DEFAULT TRUE,
                currency_notifications BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')

        await conn.close()
        print("Таблицы созданы успешно")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        raise

# Добавляем функции для работы с настройками
async def get_user_settings(user_id: int):
    """Получает настройки пользователя"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        settings = await conn.fetchrow(
            'SELECT * FROM user_settings WHERE user_id = $1',
            user_id
        )
        await conn.close()

        if settings:
            return dict(settings)
        else:
            # Создаем настройки по умолчанию
            return await create_default_settings(user_id)

    except Exception as e:
        print(f"Ошибка при получении настроек пользователя: {e}")
        return await create_default_settings(user_id)

async def create_default_settings(user_id: int):
    """Создает настройки по умолчанию для пользователя"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('''
            INSERT INTO user_settings (user_id, weather_notifications, currency_notifications)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
        ''', user_id, True, True)
        await conn.close()

        return {
            'user_id': user_id,
            'weather_notifications': True,
            'currency_notifications': True
        }
    except Exception as e:
        print(f"Ошибка при создании настроек по умолчанию: {e}")
        return {
            'user_id': user_id,
            'weather_notifications': True,
            'currency_notifications': True
        }

async def update_weather_notifications(user_id: int, enabled: bool):
    """Обновляет настройки уведомлений о погоде"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('''
            INSERT INTO user_settings (user_id, weather_notifications, updated_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id)
            DO UPDATE SET
                weather_notifications = $2,
                updated_at = CURRENT_TIMESTAMP
        ''', user_id, enabled)
        await conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении настроек погоды: {e}")
        return False

async def get_users_with_weather_notifications():
    """Получает всех пользователей с включенными уведомлениями о погоде"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        users = await conn.fetch('''
            SELECT user_id FROM user_settings
            WHERE weather_notifications = TRUE
        ''')
        await conn.close()
        return [user['user_id'] for user in users]
    except Exception as e:
        print(f"Ошибка при получении пользователей с уведомлениями о погоде: {e}")
        return []
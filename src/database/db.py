"""
Инициализация SQLite базы данных.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from src.models.activity import Activity


class DatabaseError(Exception):
    """Базовое исключение для ошибок базы данных."""
    pass


class ActivityNotFoundError(DatabaseError):
    """Исключение для случаев, когда активность не найдена."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Исключение для ошибок подключения к базе данных."""
    pass

# Путь к базе данных
DB_PATH = Path(__file__).parent.parent.parent / "data" / "time_tracker.db"


def init_db() -> None:
    """Создаёт таблицы, если они не существуют."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Таблица активностей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            description TEXT
        )''')

        # Таблица временных слотов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            activity_id INTEGER,
            description TEXT,
            FOREIGN KEY (activity_id) REFERENCES activities (id)
        )''')

        # Таблица активных сессий (для восстановления после рестарта)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            start_time TEXT NOT NULL,
            description TEXT
        )''')

        conn.commit()

    print(f"База данных инициализирована: {DB_PATH}")


def save_activity_to_db(activity: "Activity") -> int:
    """Сохраняет завершённую активность в БД."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO activities (name, type, start_time, end_time, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    activity.name,
                    activity.activity_type.value,
                    activity.start_time.isoformat(),
                    activity.end_time.isoformat() if activity.end_time else None,
                    activity.description
                )
            )
            activity_id = cursor.lastrowid

            # Создаём временной слот
            if activity.end_time:
                cursor.execute(
                    "INSERT INTO time_slots (start_time, end_time, activity_id) "
                    "VALUES (?, ?, ?)",
                    (activity.start_time.isoformat(), activity.end_time.isoformat(), activity_id)
                )

            conn.commit()
            return activity_id
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to save activity '{activity.name}': {e}") from e


def get_active_activity_from_db(user_id: int) -> Optional["Activity"]:
    """Получает активную активность пользователя из БД."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM active_sessions WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                from src.models.activity import Activity, ActivityType
                description = row['description'] if row['description'] else None
                return Activity(
                    id=row['id'],
                    name=row['name'],
                    activity_type=ActivityType(row['type']),
                    start_time=datetime.fromisoformat(row['start_time']),
                    description=description
                )
    except sqlite3.Error as e:
        # Log the error but don't raise - return None for missing active sessions
        print(f"Database error getting active session for user {user_id}: {e}")
    except (ValueError, KeyError) as e:
        # Handle invalid data in database
        print(f"Data error in active session for user {user_id}: {e}")

    return None


def save_active_activity_to_db(user_id: int, activity: "Activity") -> None:
    """Сохраняет активную сессию в БД для восстановления после рестарта."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Используем REPLACE чтобы обновить существующую запись
            cursor.execute(
                "REPLACE INTO active_sessions (user_id, name, type, start_time, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    activity.name,
                    activity.activity_type.value,
                    activity.start_time.isoformat(),
                    activity.description
                )
            )
            conn.commit()
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to save active session for user {user_id}: {e}") from e


def delete_active_activity_from_db(user_id: int) -> None:
    """Удаляет активную сессию из БД."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_sessions WHERE user_id = ?", (user_id,))
            conn.commit()
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to delete active session for user {user_id}: {e}") from e


def get_all_active_sessions() -> List[Tuple[int, "Activity"]]:
    """Получает все активные сессии из БД."""
    from src.models.activity import Activity, ActivityType

    sessions = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM active_sessions")
            rows = cursor.fetchall()

            for row in rows:
                # sqlite3.Row поддерживает доступ по ключу через []
                description = row['description'] if row['description'] else None
                activity = Activity(
                    id=row['id'],
                    name=row['name'],
                    activity_type=ActivityType(row['type']),
                    start_time=datetime.fromisoformat(row['start_time']),
                    description=description
                )
                sessions.append((row['user_id'], activity))
    except sqlite3.Error as e:
        print(f"Database error loading active sessions: {e}")
        raise DatabaseError(f"Failed to load active sessions: {e}") from e
    except (ValueError, KeyError) as e:
        print(f"Data error in active sessions: {e}")
        raise DatabaseError(f"Invalid data in active sessions: {e}") from e

    return sessions

"""
Инициализация SQLite базы данных.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Путь к базе данных
DB_PATH = Path(__file__).parent.parent.parent / "data" / "time_tracker.db"


def init_db():
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


def save_activity_to_db(activity) -> int:
    """Сохраняет завершённую активность в БД."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO activities (name, type, start_time, end_time, description) VALUES (?, ?, ?, ?, ?)",
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
                    "INSERT INTO time_slots (start_time, end_time, activity_id) VALUES (?, ?, ?)",
                    (activity.start_time.isoformat(), activity.end_time.isoformat(), activity_id)
                )
            
            conn.commit()
            return activity_id
    except Exception as e:
        raise Exception(f"Ошибка сохранения активности: {e}")


def get_active_activity_from_db(user_id: int):
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
    except Exception as e:
        print(f"Ошибка получения активной сессии: {e}")
    
    return None


def save_active_activity_to_db(user_id: int, activity):
    """Сохраняет активную сессию в БД для восстановления после рестарта."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Используем REPLACE чтобы обновить существующую запись
            cursor.execute(
                "REPLACE INTO active_sessions (user_id, name, type, start_time, description) VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    activity.name,
                    activity.activity_type.value,
                    activity.start_time.isoformat(),
                    activity.description
                )
            )
            conn.commit()
    except Exception as e:
        print(f"Ошибка сохранения активной сессии: {e}")


def delete_active_activity_from_db(user_id: int):
    """Удаляет активную сессию из БД."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_sessions WHERE user_id = ?", (user_id,))
            conn.commit()
    except Exception as e:
        print(f"Ошибка удаления активной сессии: {e}")


def get_all_active_sessions() -> List:
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
    except Exception as e:
        print(f"Ошибка загрузки активных сессий: {e}")
    
    return sessions

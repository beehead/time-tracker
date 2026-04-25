"""
Инициализация SQLite базы данных.
"""

import sqlite3
import os
from pathlib import Path

# Путь к базе данных
DB_PATH = Path("data/time_tracker.db")


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
        
        conn.commit()
    
    print(f"База данных инициализирована: {DB_PATH}")

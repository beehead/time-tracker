"""
Интеграционные тесты для работы с базой данных.
"""

import os
import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from src.models.activity import Activity, ActivityType
from src.database.db import init_db, save_activity_to_db, get_active_activity_from_db, save_active_activity_to_db, delete_active_activity_from_db, DB_PATH

# Тестовая база данных в памяти
TEST_DB_PATH = Path("/tmp/test_time_tracker.db")

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Инициализация и очистка базы данных перед каждым тестом."""
    # Удаляем старую тестовую БД, если есть
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    
    # Подменяем путь к БД
    with pytest.MonkeyPatch().context() as m:
        m.setattr("src.database.db.DB_PATH", TEST_DB_PATH)
        init_db()
        yield
    
    # Очистка после тестов
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def test_init_db_creates_tables():
    """Проверка, что init_db создаёт все таблицы."""
    with sqlite3.connect(TEST_DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Проверяем таблицу activities
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
        assert cursor.fetchone() is not None
        
        # Проверяем таблицу time_slots
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_slots'")
        assert cursor.fetchone() is not None
        
        # Проверяем таблицу active_sessions
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='active_sessions'")
        assert cursor.fetchone() is not None


def test_save_activity_to_db():
    """Проверка сохранения активности в БД."""
    activity = Activity(name="Тест", activity_type=ActivityType.PRODUCTIVE)
    activity_id = save_activity_to_db(activity)
    
    with sqlite3.connect(TEST_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row["name"] == "Тест"
        assert row["type"] == "productive"
        assert row["start_time"] is not None


def test_save_and_get_active_activity():
    """Проверка сохранения и получения активной сессии."""
    activity = Activity(name="Активная", activity_type=ActivityType.INVESTMENT)
    user_id = 123456
    
    # Сохраняем
    save_active_activity_to_db(user_id, activity)
    
    # Получаем
    retrieved = get_active_activity_from_db(user_id)
    
    assert retrieved is not None
    assert retrieved.name == "Активная"
    assert retrieved.activity_type == ActivityType.INVESTMENT


def test_delete_active_activity():
    """Проверка удаления активной сессии."""
    activity = Activity(name="Удалить", activity_type=ActivityType.EXTRAVAGANT)
    user_id = 654321
    
    save_active_activity_to_db(user_id, activity)
    assert get_active_activity_from_db(user_id) is not None
    
    delete_active_activity_from_db(user_id)
    assert get_active_activity_from_db(user_id) is None
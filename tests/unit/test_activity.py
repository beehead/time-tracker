"""
Тесты для модели Activity.
"""

import pytest
from datetime import datetime, timedelta
from src.models.activity import Activity, ActivityType


def test_activity_creation():
    """Проверка создания активности."""
    activity = Activity(name="Тестовая активность", activity_type=ActivityType.PRODUCTIVE)
    
    assert activity.name == "Тестовая активность"
    assert activity.activity_type == ActivityType.PRODUCTIVE
    assert activity.start_time is not None
    assert activity.end_time is None
    assert activity.duration is None


def test_activity_with_description():
    """Проверка активности с описанием."""
    activity = Activity(
        name="Тест",
        activity_type=ActivityType.INVESTMENT,
        description="Описание активности"
    )
    
    assert activity.description == "Описание активности"


def test_activity_duration():
    """Проверка расчёта длительности."""
    start_time = datetime.now() - timedelta(minutes=30)
    end_time = datetime.now()
    
    activity = Activity(
        name="Тест",
        activity_type=ActivityType.PRODUCTIVE,
        start_time=start_time,
        end_time=end_time
    )
    
    assert abs(activity.duration - 30 * 60) < 0.1  # 30 минут в секундах с допустимой погрешностью из-за временной задержки


def test_activity_duration_no_end():
    """Проверка расчёта длительности при отсутствии end_time."""
    activity = Activity(name="Тест", activity_type=ActivityType.PRODUCTIVE)
    activity.end_time = None
    
    assert activity.duration is None


def test_activity_repr():
    """Проверка строкового представления."""
    activity = Activity(name="Тест", activity_type=ActivityType.PRODUCTIVE)
    repr_str = repr(activity)
    
    assert "Activity" in repr_str
    assert "Тест" in repr_str
    assert "productive" in repr_str

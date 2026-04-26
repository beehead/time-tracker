"""
Тесты для модели TimeSlot.
"""

from datetime import datetime, timedelta

from src.models.time_slot import TimeSlot


def test_timeslot_creation():
    """Проверка создания временного слота."""
    slot = TimeSlot(start_time=datetime.now(), activity_id=1)

    assert slot.start_time is not None
    assert slot.end_time is None
    assert slot.activity_id == 1
    assert slot.description is None
    assert slot.duration is None


def test_timeslot_with_description():
    """Проверка слота с описанием."""
    slot = TimeSlot(
        start_time=datetime.now(),
        activity_id=1,
        description="Тестовое описание"
    )

    assert slot.description == "Тестовое описание"


def test_timeslot_duration():
    """Проверка расчёта длительности слота."""
    start_time = datetime.now() - timedelta(minutes=15)
    end_time = datetime.now()

    slot = TimeSlot(
        start_time=start_time,
        end_time=end_time,
        activity_id=1
    )

    assert abs(slot.duration - 15 * 60) < 0.1
# 15 минут в секундах с допустимой погрешностью из-за временной задержки


def test_timeslot_duration_no_end():
    """Проверка длительности при отсутствии end_time."""
    slot = TimeSlot(start_time=datetime.now(), activity_id=1)
    slot.end_time = None

    assert slot.duration is None


def test_timeslot_repr():
    """Проверка строкового представления."""
    slot = TimeSlot(start_time=datetime.now(), activity_id=1)
    repr_str = repr(slot)

    assert "TimeSlot" in repr_str
    assert "activity_id=1" in repr_str

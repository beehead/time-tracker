"""
Модель временного окна (слота времени).
"""

from datetime import datetime
from typing import Optional

class TimeSlot:
    def __init__(
        self,
        id: Optional[int] = None,
        start_time: datetime = None,
        end_time: Optional[datetime] = None,
        activity_id: Optional[int] = None,
        description: Optional[str] = None
    ):
        self.id = id
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.activity_id = activity_id
        self.description = description

    @property
    def duration(self) -> Optional[float]:
        """Возвращает продолжительность слота в секундах."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    def __repr__(self) -> str:
        return f"<TimeSlot id={self.id} start={self.start_time} end={self.end_time} duration={self.duration}s activity_id={self.activity_id}>"

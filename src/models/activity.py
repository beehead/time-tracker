"""
Модель для описания акта работы или эпизода активности.
"""

from enum import Enum
from datetime import datetime
from typing import Optional

class ActivityType(Enum):
    PRODUCTIVE = "productive"        # Продуктивная активность
    INVESTMENT = "investment"        # Инвестиционная активность
    EXTRAVAGANT = "extravagant"      # Лишняя активность
    ACTIVE_REST = "active_rest"      # Активный отдых
    HOUSEHOLD = "household"          # Дом и быт
    MAINTENANCE = "maintenance"      # Минимальное техобслуживание


class Activity:
    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        activity_type: ActivityType = ActivityType.PRODUCTIVE,
        start_time: datetime = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.activity_type = activity_type
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.description = description

    @property
    def duration(self) -> Optional[float]:
        """Возвращает продолжительность активности в секундах."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    def __repr__(self) -> str:
        return f"<Activity id={self.id} name='{self.name}' type={self.activity_type.value} start={self.start_time} end={self.end_time} duration={self.duration}s>"

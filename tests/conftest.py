"""
Конфигурация pytest.
"""


# Добавляем директорию src в sys.path для импорта
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def pytest_configure(config):
    """Выполняется перед запуском тестов."""
    pass


def pytest_unconfigure(config):
    """Выполняется после всех тестов."""
    pass

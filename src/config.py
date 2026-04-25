"""
Конфигурация приложения.
Загружает переменные окружения с валидацией.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Базовая конфигурация."""
    
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Проверяет наличие обязательных переменных."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError(
                "❌ TELEGRAM_BOT_TOKEN не задана в переменных окружения.\n"
                "Решение:\n"
                "  1. Скопируйте .env.example в .env: cp .env.example .env\n"
                "  2. Добавьте ваш токен в .env файл\n"
                "  3. Получить токен: https://t.me/BotFather"
            )


# Валидация при импорте
try:
    Config.validate()
except ValueError as e:
    print(f"\n{e}\n")
    raise


# Для удобства экспорта
TELEGRAM_TOKEN = Config.TELEGRAM_BOT_TOKEN
DEBUG = Config.DEBUG

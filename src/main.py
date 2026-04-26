#!/usr/bin/env python3
"""
Main module for the project.
"""

def main():
    """Инициализация приложения и запуск бота."""
    from src.database.db import init_db
    from src.messaging.bot import start_bot

    init_db()
    start_bot()


if __name__ == "__main__":
    main()

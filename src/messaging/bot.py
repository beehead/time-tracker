"""
Telegram Bot для учёта времени с использованием polling.

Бот периодически проверяет новые сообщения у Telegram API.
Не требует публичного IP или домена.

Перед запуском:
1. Установите зависимости: pip install -r requirements.txt
2. Создайте .env на основе .env.example: cp .env.example .env
3. Добавьте TELEGRAM_BOT_TOKEN в .env (получить у @BotFather)
4. Запустите: python -m src.main
"""

import requests
import time
import logging
from datetime import datetime
from typing import Optional, Dict
from src.models.activity import Activity, ActivityType
from src.database.db import DB_PATH, DatabaseError
from src.config import TELEGRAM_TOKEN
import sqlite3

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Настройки Telegram API
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Хранилище текущих активностей по пользователям
# Формат: { user_id: Activity }
current_activities: Dict[int, Activity] = {}

# Соответствие текста и типа активности
type_mapping = {
    "продуктивная": ActivityType.PRODUCTIVE,
    "инвестиционная": ActivityType.INVESTMENT,
    "лишняя": ActivityType.EXTRAVAGANT,
    "отдых": ActivityType.ACTIVE_REST,
    "дом": ActivityType.HOUSEHOLD,
    "техобслуживание": ActivityType.MAINTENANCE,
}


def send_message(chat_id: int, text: str, retry_count: int = 3) -> bool:
    """Отправка сообщения в чат с retry-логикой."""
    for attempt in range(retry_count):
        try:
            response = requests.post(
                f"{API_URL}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10
            )
            if response.ok:
                logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
                return True
            else:
                logger.error(f"❌ Ошибка отправки (попытка {attempt + 1}/{retry_count}): {response.text}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Сетевая ошибка (попытка {attempt + 1}/{retry_count}): {e}")
        
        if attempt < retry_count - 1:
            time.sleep(2 ** attempt)  # Экспоненциальная задержка
    
    logger.error(f"❌ Не удалось отправить сообщение после {retry_count} попыток")
    return False


def handle_message(chat_id: int, user_id: int, text: str):
    """Обработка входящего сообщения."""
    text = text.strip()
    
    if text == "/start":
        send_message(
            chat_id,
            "👋 Привет! Я бот для учёта времени.\n\n"
            "<b>Команды:</b>\n"
            "/start_activity &lt;название&gt; [тип] — начать активность\n"
            "/stop_activity — остановить\n"
            "/status — текущая активность\n"
            "/export — экспорт всех данных\n\n"
            "<b>Типы активности:</b>\n"
            "продуктивная, инвестиционная, лишняя, отдых, дом, техобслуживание"
        )
    
    elif text.startswith("/start_activity"):
        parts = text[len("/start_activity"):].strip().split(" ", 1)
        if not parts or not parts[0]:
            send_message(
                chat_id,
                "❌ Использование: /start_activity &lt;название&gt; [тип]\n"
                "Типы: продуктивная, инвестиционная, лишняя, отдых, дом, техобслуживание"
            )
            return
        
        name = parts[0]
        activity_type = ActivityType.PRODUCTIVE
        if len(parts) > 1:
            type_text = parts[1].lower()
            if type_text not in type_mapping:
                valid_types = ", ".join(type_mapping.keys())
                send_message(
                    chat_id,
                    f"❌ Неизвестный тип '{type_text}'.\n"
                    f"Допустимые типы: {valid_types}"
                )
                return
            activity_type = type_mapping[type_text]
        
        # Останавливаем предыдущую активность, если есть
        if user_id in current_activities:
            send_message(chat_id, "⏹️ Предыдущая активность остановлена.")
            stop_current_activity(user_id, chat_id)
        
        # Создаём новую
        activity = Activity(name=name, activity_type=activity_type)
        current_activities[user_id] = activity
        
        # Сохраняем в БД как активную сессию
        save_active_activity_to_db(user_id, activity)
        
        send_message(
            chat_id,
            f"▶️ Активность начата: <b>{activity.name}</b> ({activity.activity_type.value})\n"
            f"Время: {activity.start_time.strftime('%H:%M:%S')}"
        )
    
    elif text == "/stop_activity":
        if user_id not in current_activities:
            # Проверяем, есть ли активная активность в БД (на случай рестарта)
            active_from_db = get_active_activity_from_db(user_id)
            if active_from_db:
                # Восстанавливаем из БД в память
                current_activities[user_id] = active_from_db
                send_message(chat_id, "🔄 Найдена активная активность после рестарта. Останавливаю...")
                stop_current_activity(user_id, chat_id)
            else:
                send_message(chat_id, "❌ Нет активной активности.")
        else:
            stop_current_activity(user_id, chat_id)
    
    elif text == "/status":
        # Сначала проверяем память, потом БД
        act = current_activities.get(user_id)
        if not act:
            act = get_active_activity_from_db(user_id)
            if act:
                current_activities[user_id] = act
        
        if act:
            duration = (datetime.now() - act.start_time).total_seconds()
            send_message(
                chat_id,
                f"🕐 <b>Текущая активность:</b>\n"
                f"Название: {act.name}\n"
                f"Тип: {act.activity_type.value}\n"
                f"Началась: {act.start_time.strftime('%H:%M:%S')}\n"
                f"Прошло: {int(duration // 60)}м {int(duration % 60)}с"
            )
        else:
            send_message(chat_id, "❌ Нет активной активности.")
    
    elif text == "/export":
        export_data(chat_id)
    
    else:
        send_message(chat_id, "❓ Неизвестная команда. Введи /start для справки.")


def stop_current_activity(user_id: int, chat_id: int):
    """Останавливает текущую активность и сохраняет в БД."""
    activity = current_activities.pop(user_id)
    activity.end_time = datetime.now()
    
    # Сохранение в БД
    try:
        from src.database.db import save_activity_to_db, delete_active_activity_from_db
        
        activity_id = save_activity_to_db(activity)
        
        # Удаляем активную сессию из БД
        delete_active_activity_from_db(user_id)
        
        duration_seconds = activity.duration
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        send_message(
            chat_id,
            f"✅ Активность сохранена (ID: {activity_id})\n"
            f"Длительность: {minutes}м {seconds}с"
        )
    except DatabaseError as e:
        logger.error(f"❌ Database error saving activity: {e}")
        send_message(chat_id, "❌ Ошибка базы данных. Попробуйте позже.")
        # Restore the activity in memory since saving failed
        current_activities[user_id] = activity
    except Exception as e:
        logger.error(f"❌ Unexpected error saving activity: {e}")
        send_message(chat_id, f"❌ Неожиданная ошибка: {e}")
        # Restore the activity in memory since saving failed
        current_activities[user_id] = activity


def get_active_activity_from_db(user_id: int) -> Optional[Activity]:
    """Получает активную активность пользователя из БД."""
    from src.database.db import get_active_activity_from_db as db_get_active
    return db_get_active(user_id)


def save_active_activity_to_db(user_id: int, activity: Activity):
    """Сохраняет активную сессию в БД для восстановления после рестарта."""
    try:
        from src.database.db import save_active_activity_to_db as db_save_active
        db_save_active(user_id, activity)
    except DatabaseError as e:
        logger.error(f"Failed to save active session for user {user_id}: {e}")
        raise


def delete_active_activity_from_db(user_id: int):
    """Удаляет активную сессию из БД."""
    try:
        from src.database.db import delete_active_activity_from_db as db_delete_active
        db_delete_active(user_id)
    except DatabaseError as e:
        logger.error(f"Failed to delete active session for user {user_id}: {e}")
        raise


def export_data(chat_id: int):
    """Экспорт всех данных в текстовом виде."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.id, a.name, a.type, a.start_time, a.end_time,
                       t.id as slot_id
                FROM activities a
                LEFT JOIN time_slots t ON a.id = t.activity_id
                ORDER BY a.start_time DESC
            ''')
            rows = cursor.fetchall()
        
        if not rows:
            send_message(chat_id, "❌ Нет данных для экспорта.")
            return
        
        export_text = "📊 <b>Экспорт данных учёта времени:</b>\n\n"
        for row in rows:
            start = row['start_time'][:10]  # Дата
            time_start = row['start_time'][11:19]  # Время
            time_end = row['end_time'][11:19] if row['end_time'] else "—"
            export_text += f"• [{row['type']}] {row['name']}\n  {start} {time_start}→{time_end}\n"
        
        # Обрезаем, если слишком длинный
        if len(export_text) > 4000:
            export_text = export_text[:4000] + "\n... (обрезано)"
        
        send_message(chat_id, export_text)
    
    except Exception as e:
        send_message(chat_id, f"❌ Ошибка экспорта: {e}")


def get_updates(offset: int = 0, timeout: int = 30) -> list:
    """Получить обновления от Telegram с retry-логикой."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{API_URL}/getUpdates",
                params={"offset": offset, "timeout": timeout},
                timeout=timeout + 5
            )
            if response.ok:
                return response.json().get("result", [])
            else:
                logger.error(f"❌ Ошибка getUpdates (попытка {attempt + 1}/{max_retries}): {response.text}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Сетевая ошибка getUpdates (попытка {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return []


def start_bot():
    """Запуск бота с использованием polling."""
    logger.info("🤖 Бот запущен. Ожидание сообщений...")
    offset = 0
    
    # Загружаем активные сессии из БД при старте
    load_active_sessions_from_db()
    
    try:
        while True:
            updates = get_updates(offset)
            
            for update in updates:
                if "message" in update:
                    message = update["message"]
                    chat_id = message["chat"]["id"]
                    user_id = message["from"]["id"]
                    text = message.get("text", "")
                    
                    logger.info(f"📨 [{user_id}] {text}")
                    handle_message(chat_id, user_id, text)
                
                # КРИТИЧЕСКИ ВАЖНО: обновляем offset для следующей итерации
                # Это предотвращает потерю сообщений
                offset = update["update_id"] + 1
            
            # Небольшая задержка чтобы не перегружать API
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен пользователем.")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в основном цикле: {e}", exc_info=True)
        raise


def load_active_sessions_from_db():
    """Загружает все активные сессии из БД при старте бота."""
    try:
        from src.database.db import get_all_active_sessions
        
        sessions = get_all_active_sessions()
        for user_id, activity in sessions:
            current_activities[user_id] = activity
            logger.info(f"🔄 Восстановлена активная сессия для пользователя {user_id}: {activity.name}")
    except DatabaseError as e:
        logger.error(f"Failed to load active sessions from database: {e}")
        logger.warning("Bot will start without loading previous active sessions")
    except Exception as e:
        logger.error(f"Unexpected error loading active sessions: {e}")
        logger.warning("Bot will start without loading previous active sessions")


# Для запуска: python -m src.main
if __name__ == "__main__":
    start_bot()
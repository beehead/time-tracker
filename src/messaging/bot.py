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
from datetime import datetime
from src.models.activity import Activity, ActivityType
from src.database.db import DB_PATH
from src.config import TELEGRAM_TOKEN
import sqlite3

# Настройки Telegram API
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Хранилище текущих активностей по пользователям
# Формат: { user_id: Activity }
current_activities = {}

# Соответствие текста и типа активности
type_mapping = {
    "продуктивная": ActivityType.PRODUCTIVE,
    "инвестиционная": ActivityType.INVESTMENT,
    "лишняя": ActivityType.EXTRAVAGANT,
    "отдых": ActivityType.ACTIVE_REST,
    "дом": ActivityType.HOUSEHOLD,
    "техобслуживание": ActivityType.MAINTENANCE,
}


def send_message(chat_id: int, text: str):
    """Отправка сообщения в чат."""
    response = requests.post(
        f"{API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    )
    if not response.ok:
        print(f"❌ Ошибка отправки: {response.text}")
    else:
        print(f"✅ Сообщение отправлено в чат {chat_id}")


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
            activity_type = type_mapping.get(type_text, ActivityType.PRODUCTIVE)
        
        # Останавливаем предыдущую активность, если есть
        if user_id in current_activities:
            send_message(chat_id, "⏹️ Предыдущая активность остановлена.")
            stop_current_activity(user_id, chat_id)
        
        # Создаём новую
        activity = Activity(name=name, activity_type=activity_type)
        current_activities[user_id] = activity
        send_message(
            chat_id,
            f"▶️ Активность начата: <b>{activity.name}</b> ({activity.activity_type.value})\n"
            f"Время: {activity.start_time.strftime('%H:%M:%S')}"
        )
    
    elif text == "/stop_activity":
        if user_id not in current_activities:
            send_message(chat_id, "❌ Нет активной активности.")
        else:
            stop_current_activity(user_id, chat_id)
    
    elif text == "/status":
        if user_id in current_activities:
            act = current_activities[user_id]
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
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO activities (name, type, start_time, end_time, description) VALUES (?, ?, ?, ?, ?)",
                (
                    activity.name,
                    activity.activity_type.value,
                    activity.start_time.isoformat(),
                    activity.end_time.isoformat(),
                    activity.description
                )
            )
            activity_id = cursor.lastrowid
            # Создаём временной слот
            cursor.execute(
                "INSERT INTO time_slots (start_time, end_time, activity_id) VALUES (?, ?, ?)",
                (activity.start_time.isoformat(), activity.end_time.isoformat(), activity_id)
            )
            conn.commit()
        
        duration_seconds = activity.duration
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        send_message(
            chat_id,
            f"✅ Активность сохранена (ID: {activity_id})\n"
            f"Длительность: {minutes}м {seconds}с"
        )
    except Exception as e:
        send_message(chat_id, f"❌ Ошибка сохранения: {e}")


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


def get_updates(offset=0):
    """Получить обновления от Telegram."""
    try:
        response = requests.get(
            f"{API_URL}/getUpdates",
            params={"offset": offset, "timeout": 30}
        )
        if response.ok:
            return response.json()["result"]
        else:
            print(f"❌ Ошибка getUpdates: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return []


def start_bot():
    """Запуск бота с использованием polling."""
    print("🤖 Бот запущен. Ожидание сообщений...")
    offset = 0
    
    try:
        while True:
            updates = get_updates(offset)
            
            for update in updates:
                if "message" in update:
                    message = update["message"]
                    chat_id = message["chat"]["id"]
                    user_id = message["from"]["id"]
                    text = message.get("text", "")
                    
                    print(f"📨 [{user_id}] {text}")
                    handle_message(chat_id, user_id, text)
                
                # Обновляем offset для следующей итерации
                offset = update["update_id"] + 1
            
            # Небольшая задержка чтобы не перегружать API
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен.")
    except Exception as e:
        print(f"❌ Ошибка в основном цикле: {e}")
        raise


# Для запуска: python -m src.main
if __name__ == "__main__":
    start_bot()
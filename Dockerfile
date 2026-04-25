# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости системы (если потребуются)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Создаём папку для данных
RUN mkdir -p data

# Выставляем переменную окружения для Python (без буферизации вывода)
ENV PYTHONUNBUFFERED=1

# Команда для запуска приложения
CMD ["python", "-m", "src.main"]

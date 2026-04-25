# Запуск в Docker

## Способ 1: Docker Compose (рекомендуется)

### Установка Docker и Docker Compose

**macOS/Windows:**

- Установите [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Docker Compose включен в Docker Desktop

**Linux:**

```bash
# Установка Docker
sudo apt-get install docker.io

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Запуск бота

1. **Создайте `.env` файл:**

   ```bash
   cp .env.docker.example .env
   ```

2. **Добавьте токен в `.env`:**

   ```bash
   # Отредактируйте .env и добавьте:
   TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
   ```

3. **Запустите контейнер:**

   ```bash
   docker-compose up -d
   ```

4. **Проверьте логи:**

   ```bash
   docker-compose logs -f time-tracker-bot
   ```

5. **Остановка:**

   ```bash
   docker-compose down
   ```

### Полезные команды

```bash
# Просмотр логов в реальном времени
docker-compose logs -f time-tracker-bot

# Просмотр последних 100 строк логов
docker-compose logs --tail=100 time-tracker-bot

# Перезапуск контейнера
docker-compose restart time-tracker-bot

# Пересборка образа
docker-compose up -d --build

# Полная очистка (удаляет контейнер и тома)
docker-compose down -v
```

---

## Способ 2: Ручная сборка Docker образа

### Сборка образа

```bash
docker build -t time-tracker-bot:latest .
```

### Запуск контейнера

```bash
docker run -d \
  --name time-tracker-bot \
  -e TELEGRAM_BOT_TOKEN="ваш_токен" \
  -v ./data:/app/data \
  --restart unless-stopped \
  time-tracker-bot:latest
```

### Просмотр логов

```bash
docker logs -f time-tracker-bot
```

---

## Файловая система в контейнере

- `/app` — рабочая директория приложения
- `/app/data` — база данных `time_tracker.db` (смонтирована как том)
- Том `./data` на хосте связан с `/app/data` в контейнере

**Данные сохраняются между перезагрузками!**

---

## Переменные окружения

| Переменная           | Обязательна | Описание                  |
|----------------------|-------------|--------------------------|
| `TELEGRAM_BOT_TOKEN` | ✅ Да      | Токен бота от @BotFather |

---

## Отладка

### Контейнер не запускается

```bash
# Проверьте логи
docker-compose logs time-tracker-bot

# Проверьте, что .env заполнен
cat .env
```

### Нет пермиссий на том

```bash
# Измените пермиссии на папку data
chmod 777 data
```

### Переересборка образа

```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## Production развертывание

Для production рекомендуется:

1. **Использовать Docker registry** (Docker Hub, GitLab Registry и т.д.)
2. **Настроить мониторинг** (Prometheus, Grafana)
3. **Добавить health checks**
4. **Использовать secrets management** (Docker Secrets, Vault)
5. **Настроить логирование** (ELK Stack, CloudWatch)

### Пример с health check

```yaml
services:
  time-tracker-bot:
    build: .
    container_name: time-tracker-bot
    environment:
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('https://api.telegram.org/bot/getMe')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Проблемы и решения

### Error: Cannot connect to Docker daemon

```bash
# Linux: добавьте себя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# macOS/Windows: перезагрузите Docker Desktop
```

### Error: Port already in use

```bash
# Docker Compose не использует внешние порты, но если нужно:
# Измените в docker-compose.yml
ports:
  - "5000:5000"
```

### Свободное место на диске

```bash
# Очистка неиспользуемых образов
docker image prune -a

# Очистка неиспользуемых томов
docker volume prune

# Полная очистка
docker system prune -a
```

---

## Ссылки

- [Docker документация](https://docs.docker.com/)
- [Docker Compose документация](https://docs.docker.com/compose/)
- [Best practices для Docker](https://docs.docker.com/develop/dev-best-practices/)

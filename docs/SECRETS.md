# Хранение секретов и конфиденциальных данных

## Принципы безопасности

1. **Никогда не коммитьте секреты** в репозиторий
2. **Используйте переменные окружения** для конфиденциальных данных
3. **Создавайте `.env.example`** как шаблон без реальных значений
4. **Исключайте `.env` файлы** в `.gitignore`

## Методы хранения секретов

### 1. Локальные переменные окружения (`.env` файл)

#### Для разработки и тестирования

```bash
# .env (создать вручную, не коммитить!)
TELEGRAM_BOT_TOKEN=123456789:ABCDefGhIjKlMnOpQrStUvWxYz1234567890
```

#### Загрузка в Python

```python
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
```

#### Преимущества и недостатки

**Преимущества:**

- ✅ Просто для локальной разработки
- ✅ Работает с `python-dotenv`

**Недостатки:**

- ❌ Опасно для production
- ❌ Легко случайно закоммитить
- ❌ Неудобно для teamwork

### 2. Системные переменные окружения

#### Для production серверов (Linux/macOS)

```bash
# На сервере
export TELEGRAM_BOT_TOKEN="ваш_токен"

# Или в файле /etc/environment
TELEGRAM_BOT_TOKEN=ваш_токен

# Или в systemd unit file
[Service]
Environment="TELEGRAM_BOT_TOKEN=ваш_токен"
```

### 3. Менеджеры секретов (для production)

#### AWS Secrets Manager

```python
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='telegram_bot_token')
token = secret['SecretString']
```

#### HashiCorp Vault

```python
import hvac
client = hvac.Client(url='http://127.0.0.1:8200')
token = client.secrets.kv.read_secret_version(path='telegram_bot')
```

#### GitHub Secrets (для CI/CD)

```yaml
# .github/workflows/deploy.yml
env:
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
```

### 4. `.env.local` для командной разработки

```bash
# .env.local (локальные переопределения, не коммитить!)
# Переопределяет значения из .env.example
TELEGRAM_BOT_TOKEN=my_personal_token_for_testing
```

## Структура файлов

```bash
project/
├── .env.example          # ✅ КОММИТЬТЕ (шаблон без значений)
├── .env                  # ❌ НЕ КОММИТЬТЕ (реальные секреты)
├── .env.local            # ❌ НЕ КОММИТЬТЕ (локальные переопределения)
├── .gitignore           # ✅ КОММИТЬТЕ (исключает .env*)
└── .env.production       # ❌ ТОЛЬКО НА СЕРВЕРЕ
```

## Проверка `.gitignore`

```bash
# Проверить, что .env не отслеживается
git check-ignore .env
# Выведет: .env (если правильно исключен)

# Если .env уже в репозитории, удалить его:
git rm --cached .env
git commit -m "Remove .env from tracking"
```

## Пример использования в коде

```python
# ✅ ПРАВИЛЬНО
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задана в переменных окружения")

# ❌ НЕПРАВИЛЬНО
TELEGRAM_TOKEN = "123456789:ABCDefGhIjKlMnOpQrStUvWxYz1234567890"  # Никогда!
```

## Для CI/CD (GitHub Actions пример)

```yaml
name: Deploy
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Run bot
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        run: python -m src.main
```

## Чеклист безопасности

- [ ] `.env` добавлен в `.gitignore`
- [ ] `.env.example` создан и закоммичен
- [ ] Нет реальных токенов в коде
- [ ] `python-dotenv` установлен (`pip install python-dotenv`)
- [ ] Переменные загружаются через `os.getenv()`
- [ ] Проверка наличия обязательных переменных
- [ ] Логирование НЕ содержит секретов

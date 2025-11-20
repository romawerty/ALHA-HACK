# Быстрый старт

## Вариант 1: Запуск через Docker (рекомендуется)

### Шаг 1: Настройка переменных окружения

1. Скопируйте `env.example` в `.env`:
   ```bash
   cp env.example .env
   ```

2. Откройте `.env` и заполните необходимые значения:
   ```env
   # Обязательно измените!
   JWT_SECRET_KEY=ваш-длинный-секретный-ключ-минимум-32-символа-для-безопасности
   
   # Получите на https://oauth.yandex.ru/ (см. YANDEX_API_SETUP.md)
   YANDEX_CALENDAR_CLIENT_ID=ваш_client_id
   YANDEX_CALENDAR_CLIENT_SECRET=ваш_client_secret
   YANDEX_EMAIL_CLIENT_ID=ваш_client_id
   YANDEX_EMAIL_CLIENT_SECRET=ваш_client_secret
   
   # Опционально (для улучшенной работы LLM)
   HUGGINGFACE_API_KEY=ваш_huggingface_ключ
   ```

### Шаг 2: Получение API ключей Яндекс

Следуйте инструкциям в файле `YANDEX_API_SETUP.md`

**Кратко:**
1. Перейдите на https://oauth.yandex.ru/
2. Создайте приложение
3. Укажите Redirect URI: `http://localhost:8000/auth/yandex/callback`
4. Включите права: `calendar:read`, `calendar:write`, `mail:read`, `mail:write`
5. Скопируйте Client ID и Client Secret

### Шаг 3: Запуск

```bash
docker-compose up --build
```

### Шаг 4: Открытие приложения

Откройте браузер и перейдите на:
- **Frontend**: http://localhost:8501
- **API Gateway**: http://localhost:8000/health (для проверки)

### Шаг 5: Первый вход

1. Нажмите "Регистрация"
2. Заполните форму (имя, email, пароль)
3. После регистрации вы автоматически войдете в систему

## Вариант 2: Локальный запуск (без Docker)

### Требования

- Python 3.11+
- Все зависимости из requirements.txt каждого сервиса

### Установка зависимостей

```bash
# Для каждого сервиса
cd services/api-gateway && pip install -r requirements.txt && cd ../..
cd services/auth-service && pip install -r requirements.txt && cd ../..
cd services/calendar-service && pip install -r requirements.txt && cd ../..
cd services/email-service && pip install -r requirements.txt && cd ../..
cd services/news-service && pip install -r requirements.txt && cd ../..
cd services/llm-agent-service && pip install -r requirements.txt && cd ../..
cd frontend && pip install -r requirements.txt && cd ../..
```

### Запуск

Используйте скрипт `run_local.py`:

```bash
python run_local.py
```

Или запускайте каждый сервис вручную в отдельных терминалах:

```bash
# Терминал 1: API Gateway
cd services/api-gateway
uvicorn main:app --port 8000

# Терминал 2: Auth Service
cd services/auth-service
uvicorn main:app --port 8001

# Терминал 3: Calendar Service
cd services/calendar-service
uvicorn main:app --port 8002

# Терминал 4: Email Service
cd services/email-service
uvicorn main:app --port 8003

# Терминал 5: News Service
cd services/news-service
uvicorn main:app --port 8004

# Терминал 6: LLM Agent Service
cd services/llm-agent-service
uvicorn main:app --port 8005

# Терминал 7: Frontend
cd frontend
streamlit run app.py --server.port=8501
```

## Проверка работы

1. Откройте http://localhost:8501
2. Зарегистрируйтесь или войдите
3. Вы должны увидеть главную страницу с 3 колонками:
   - Предстоящие встречи
   - Входящие письма
   - Финансовые новости

## Демо-режим

Если API ключи Яндекс не настроены, система будет работать в демо-режиме с заглушками:
- Показываются примеры встреч, писем и новостей
- Функции создания/удаления работают локально
- Реальная интеграция с Яндекс не работает

## Устранение проблем

### Порт уже занят

Если порт занят, измените порты в `docker-compose.yml` или остановите процесс, использующий порт.

### Ошибки подключения

1. Убедитесь, что все сервисы запущены
2. Проверьте логи: `docker-compose logs`
3. Проверьте переменные окружения в `.env`

### Ошибки авторизации Яндекс

1. Проверьте правильность Client ID и Client Secret
2. Убедитесь, что Redirect URI совпадает с настройками приложения
3. Проверьте, что включены необходимые права (scopes)

## Остановка

Для Docker:
```bash
docker-compose down
```

Для локального запуска:
- Нажмите Ctrl+C в каждом терминале
- Или используйте `pkill -f uvicorn` и `pkill -f streamlit`


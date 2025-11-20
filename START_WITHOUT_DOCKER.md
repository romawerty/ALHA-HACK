# Запуск без Docker

Если Docker не установлен или не работает, вы можете запустить систему локально.

## Предварительные требования

1. Python 3.11 или выше
2. pip (менеджер пакетов Python)

## Установка зависимостей

### Вариант 1: Автоматическая установка (рекомендуется)

Запустите скрипт установки:

```powershell
# Windows PowerShell
python install_dependencies.py
```

### Вариант 2: Ручная установка

Установите зависимости для каждого сервиса:

```powershell
# API Gateway
cd services/api-gateway
pip install -r requirements.txt
cd ../..

# Auth Service
cd services/auth-service
pip install -r requirements.txt
cd ../..

# Calendar Service
cd services/calendar-service
pip install -r requirements.txt
cd ../..

# Email Service
cd services/email-service
pip install -r requirements.txt
cd ../..

# News Service
cd services/news-service
pip install -r requirements.txt
cd ../..

# LLM Agent Service
cd services/llm-agent-service
pip install -r requirements.txt
cd ../..

# Frontend
cd frontend
pip install -r requirements.txt
cd ../..
```

## Запуск

### Вариант 1: Автоматический запуск всех сервисов

```powershell
python run_local.py
```

### Вариант 2: Ручной запуск в отдельных терминалах

Откройте 7 терминалов и запустите в каждом:

**Терминал 1 - API Gateway:**
```powershell
cd services/api-gateway
python -m uvicorn main:app --port 8000 --reload
```

**Терминал 2 - Auth Service:**
```powershell
cd services/auth-service
python -m uvicorn main:app --port 8001 --reload
```

**Терминал 3 - Calendar Service:**
```powershell
cd services/calendar-service
python -m uvicorn main:app --port 8002 --reload
```

**Терминал 4 - Email Service:**
```powershell
cd services/email-service
python -m uvicorn main:app --port 8003 --reload
```

**Терминал 5 - News Service:**
```powershell
cd services/news-service
python -m uvicorn main:app --port 8004 --reload
```

**Терминал 6 - LLM Agent Service:**
```powershell
cd services/llm-agent-service
python -m uvicorn main:app --port 8005 --reload
```

**Терминал 7 - Frontend:**
```powershell
cd frontend
streamlit run app.py --server.port=8501
```

## Проверка работы

1. Дождитесь запуска всех сервисов
2. Откройте браузер: http://localhost:8501
3. Зарегистрируйтесь или войдите

## Важные замечания

1. **Переменные окружения**: Создайте файл `.env` из `env.example` и заполните необходимые значения

2. **Порты**: Убедитесь, что порты 8000-8005 и 8501 свободны

3. **Путь к данным**: Auth Service будет создавать данные в `services/auth-service/data/` (вместо `/app/data` в Docker)

4. **Ошибки подключения**: Если фронтенд не может подключиться к API, проверьте, что все сервисы запущены

## Остановка

Нажмите `Ctrl+C` в каждом терминале, где запущен сервис.

Или используйте:
```powershell
# Остановить все процессы Python
taskkill /F /IM python.exe
```

## Устранение проблем

### Ошибка: `ModuleNotFoundError`

Установите недостающий модуль:
```powershell
pip install имя_модуля
```

### Ошибка: `Port already in use`

Найдите и остановите процесс, использующий порт:
```powershell
netstat -ano | findstr :8000
taskkill /PID <номер_процесса> /F
```

### Ошибка: `Cannot connect to API`

1. Проверьте, что все сервисы запущены
2. Проверьте URL в `frontend/app.py` (должен быть `http://localhost:8000`)
3. Проверьте логи сервисов на наличие ошибок


"""
Скрипт для локального запуска всех сервисов (без Docker)
Требует установки всех зависимостей: pip install -r requirements.txt для каждого сервиса
"""

import subprocess
import sys
import os
from pathlib import Path

def run_service(name, port, path):
    """Запуск сервиса в отдельном процессе"""
    print(f"Запуск {name} на порту {port}...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(path).parent)
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port)],
            cwd=path,
            env=env
        )
        return process
    except Exception as e:
        print(f"Ошибка запуска {name}: {e}")
        return None

def run_frontend():
    """Запуск Streamlit фронтенда"""
    print("Запуск Frontend на порту 8501...")
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501"],
            cwd="frontend"
        )
        return process
    except Exception as e:
        print(f"Ошибка запуска Frontend: {e}")
        return None

if __name__ == "__main__":
    print("Запуск всех сервисов локально...")
    print("Убедитесь, что все зависимости установлены!")
    print("=" * 50)
    
    processes = []
    
    # Запуск микросервисов
    services = [
        ("API Gateway", 8000, "services/api-gateway"),
        ("Auth Service", 8001, "services/auth-service"),
        ("Calendar Service", 8002, "services/calendar-service"),
        ("Email Service", 8003, "services/email-service"),
        ("News Service", 8004, "services/news-service"),
        ("LLM Agent Service", 8005, "services/llm-agent-service"),
    ]
    
    for name, port, path in services:
        proc = run_service(name, port, path)
        if proc:
            processes.append((name, proc))
    
    # Запуск фронтенда
    frontend_proc = run_frontend()
    if frontend_proc:
        processes.append(("Frontend", frontend_proc))
    
    print("\n" + "=" * 50)
    print("Все сервисы запущены!")
    print("Frontend доступен по адресу: http://localhost:8501")
    print("Нажмите Ctrl+C для остановки всех сервисов")
    print("=" * 50)
    
    try:
        # Ожидание завершения
        for name, proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        print("\nОстановка всех сервисов...")
        for name, proc in processes:
            proc.terminate()
        print("Все сервисы остановлены.")


"""
Скрипт для проверки системы и диагностики проблем
"""

import os
import sys
import subprocess
from pathlib import Path

def check_docker():
    """Проверка Docker"""
    print("=" * 50)
    print("Проверка Docker...")
    print("=" * 50)
    
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker установлен: {result.stdout.strip()}")
        else:
            print("❌ Docker не найден")
            return False
    except FileNotFoundError:
        print("❌ Docker не установлен")
        return False
    
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose установлен: {result.stdout.strip()}")
        else:
            print("❌ Docker Compose не найден")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose не установлен")
        return False
    
    return True

def check_files():
    """Проверка наличия файлов"""
    print("\n" + "=" * 50)
    print("Проверка файлов...")
    print("=" * 50)
    
    required_files = [
        "docker-compose.yml",
        "env.example",
        "services/api-gateway/main.py",
        "services/api-gateway/Dockerfile",
        "services/api-gateway/requirements.txt",
        "services/auth-service/main.py",
        "services/auth-service/Dockerfile",
        "services/auth-service/requirements.txt",
        "services/calendar-service/main.py",
        "services/email-service/main.py",
        "services/news-service/main.py",
        "services/llm-agent-service/main.py",
        "frontend/app.py",
        "frontend/Dockerfile",
        "frontend/requirements.txt",
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - НЕ НАЙДЕН")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Отсутствует {len(missing_files)} файлов")
        return False
    
    return True

def check_env():
    """Проверка .env файла"""
    print("\n" + "=" * 50)
    print("Проверка .env файла...")
    print("=" * 50)
    
    if not Path(".env").exists():
        print("⚠️  Файл .env не найден")
        print("💡 Создайте его из env.example: cp env.example .env")
        return False
    
    print("✅ Файл .env существует")
    
    # Проверка ключевых переменных
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()
        
    required_vars = ["JWT_SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if var in content and not content.split(var)[1].split("\n")[0].strip().startswith("your-"):
            print(f"✅ {var} настроен")
        else:
            print(f"⚠️  {var} не настроен или использует значение по умолчанию")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_ports():
    """Проверка доступности портов"""
    print("\n" + "=" * 50)
    print("Проверка портов...")
    print("=" * 50)
    
    import socket
    
    ports = [8000, 8001, 8002, 8003, 8004, 8005, 8501]
    busy_ports = []
    
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"⚠️  Порт {port} занят")
            busy_ports.append(port)
        else:
            print(f"✅ Порт {port} свободен")
    
    if busy_ports:
        print(f"\n⚠️  Занято портов: {busy_ports}")
        print("💡 Остановите процессы или измените порты в docker-compose.yml")
        return False
    
    return True

def check_python_syntax():
    """Проверка синтаксиса Python файлов"""
    print("\n" + "=" * 50)
    print("Проверка синтаксиса Python...")
    print("=" * 50)
    
    python_files = [
        "services/api-gateway/main.py",
        "services/auth-service/main.py",
        "services/calendar-service/main.py",
        "services/email-service/main.py",
        "services/news-service/main.py",
        "services/llm-agent-service/main.py",
        "frontend/app.py",
    ]
    
    errors = []
    for file_path in python_files:
        if not Path(file_path).exists():
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                compile(f.read(), file_path, "exec")
            print(f"✅ {file_path}")
        except SyntaxError as e:
            print(f"❌ {file_path}: {e}")
            errors.append((file_path, e))
        except Exception as e:
            print(f"⚠️  {file_path}: {e}")
    
    if errors:
        print(f"\n❌ Найдено {len(errors)} ошибок синтаксиса")
        return False
    
    return True

def main():
    """Главная функция"""
    print("\n" + "=" * 50)
    print("ДИАГНОСТИКА СИСТЕМЫ")
    print("=" * 50 + "\n")
    
    checks = [
        ("Docker", check_docker),
        ("Файлы", check_files),
        (".env файл", check_env),
        ("Порты", check_ports),
        ("Синтаксис Python", check_python_syntax),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Ошибка при проверке {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("ИТОГИ ПРОВЕРКИ")
    print("=" * 50)
    
    for name, result in results:
        status = "✅ ПРОЙДЕНА" if result else "❌ НЕ ПРОЙДЕНА"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ Все проверки пройдены! Система готова к запуску.")
        print("\n💡 Запустите: docker-compose up --build")
    else:
        print("\n⚠️  Некоторые проверки не пройдены. Исправьте ошибки перед запуском.")
        print("\n💡 См. TROUBLESHOOTING.md для помощи")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())


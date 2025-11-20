"""
Скрипт для автоматической установки всех зависимостей
"""

import subprocess
import sys
from pathlib import Path

def install_requirements(path):
    """Установка зависимостей из requirements.txt"""
    req_file = Path(path) / "requirements.txt"
    if not req_file.exists():
        print(f"⚠️  {req_file} не найден, пропускаю...")
        return False
    
    print(f"📦 Установка зависимостей из {path}...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {path} - зависимости установлены")
            return True
        else:
            print(f"❌ {path} - ошибка установки:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {path} - ошибка: {e}")
        return False

def main():
    """Главная функция"""
    print("=" * 50)
    print("УСТАНОВКА ЗАВИСИМОСТЕЙ")
    print("=" * 50 + "\n")
    
    services = [
        "services/api-gateway",
        "services/auth-service",
        "services/calendar-service",
        "services/email-service",
        "services/news-service",
        "services/llm-agent-service",
        "frontend",
    ]
    
    results = []
    for service in services:
        if Path(service).exists():
            success = install_requirements(service)
            results.append((service, success))
        else:
            print(f"⚠️  {service} - директория не найдена")
            results.append((service, False))
    
    print("\n" + "=" * 50)
    print("ИТОГИ УСТАНОВКИ")
    print("=" * 50)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for service, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {service}")
    
    print(f"\n✅ Успешно: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 Все зависимости установлены!")
        print("\n💡 Теперь вы можете запустить систему:")
        print("   python run_local.py")
    else:
        print("\n⚠️  Некоторые зависимости не установлены")
        print("💡 Попробуйте установить их вручную")
    
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())


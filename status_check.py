#!/usr/bin/env python3
"""
Проверка статуса всех систем Discord бота
"""

import requests
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def check_bot_health():
    """Проверка здоровья бота"""
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            return True, "Бот здоров"
        else:
            return False, f"HTTP статус {response.status_code}"
    except Exception as e:
        return False, f"Ошибка подключения: {e}"

def check_permanent_host():
    """Проверка работы постоянного хоста"""
    status_file = Path("bot_status.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            return status.get('running', False), f"PID: {status.get('pid', 'N/A')}"
        except Exception as e:
            return False, f"Ошибка чтения статуса: {e}"
    else:
        return False, "Файл статуса не найден"

def check_token():
    """Проверка токена"""
    token_file = Path("token.txt")
    if token_file.exists():
        try:
            token = token_file.read_text().strip()
            if len(token) > 50:
                return True, f"Токен найден ({len(token)} символов)"
            else:
                return False, "Токен слишком короткий"
        except Exception as e:
            return False, f"Ошибка чтения токена: {e}"
    else:
        return False, "Файл token.txt не найден"

def main():
    print("🔍 Проверка статуса Discord бота")
    print("=" * 50)
    
    checks = [
        ("Токен Discord", check_token),
        ("Постоянный хост", check_permanent_host),
        ("Здоровье бота", check_bot_health),
    ]
    
    all_good = True
    
    for name, check_func in checks:
        try:
            is_ok, message = check_func()
            status = "✅" if is_ok else "❌"
            print(f"{status} {name}: {message}")
            if not is_ok:
                all_good = False
        except Exception as e:
            print(f"❌ {name}: Ошибка проверки - {e}")
            all_good = False
    
    print("=" * 50)
    
    if all_good:
        print("🎉 Все системы работают нормально!")
        print("🌐 Веб-интерфейс: http://localhost:8080")
        return 0
    else:
        print("⚠️ Обнаружены проблемы. Проверьте логи.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
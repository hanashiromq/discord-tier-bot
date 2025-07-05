
#!/usr/bin/env python3
"""
Скрипт для запуска системы мониторинга Discord бота
Используйте этот файл если хотите запустить только мониторинг
"""

import subprocess
import sys
import time

def start_monitor():
    """Запуск мониторинга"""
    print("🚀 Запуск системы мониторинга Discord бота...")
    print("📊 Мониторинг будет доступен на:")
    print("   - http://0.0.0.0:5000 (основной мониторинг)")
    print("   - http://0.0.0.0:8080 (keep-alive сервер)")
    print("⏰ Проверки каждые 5 минут")
    print("-" * 50)
    
    try:
        # Запускаем background.py
        subprocess.run([sys.executable, "background.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска мониторинга: {e}")

if __name__ == "__main__":
    start_monitor()

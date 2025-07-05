#!/usr/bin/env python3
"""
Постоянный хост для Discord бота
Обеспечивает непрерывную работу бота 24/7
"""

import asyncio
import subprocess
import time
import os
import sys
import signal
import threading
from datetime import datetime, timedelta
import requests
import json
from pathlib import Path

class PermanentBotHost:
    def __init__(self):
        self.bot_process = None
        self.should_run = True
        self.restart_count = 0
        self.last_restart = datetime.now()
        self.status_file = Path("bot_status.json")
        self.log_file = Path("bot_host.log")
        
    def log(self, message):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # Запись в файл
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"Ошибка записи в лог: {e}")
    
    def save_status(self):
        """Сохранение статуса в файл"""
        try:
            status = {
                "running": self.bot_process is not None and self.bot_process.poll() is None,
                "restart_count": self.restart_count,
                "last_restart": self.last_restart.isoformat(),
                "uptime_start": datetime.now().isoformat(),
                "pid": self.bot_process.pid if self.bot_process else None
            }
            
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            self.log(f"Ошибка сохранения статуса: {e}")
    
    def start_bot(self):
        """Запуск бота"""
        try:
            self.log("🚀 Запуск Discord бота...")
            
            # Установка переменных окружения
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            self.bot_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env
            )
            
            self.log(f"✅ Бот запущен с PID: {self.bot_process.pid}")
            self.save_status()
            
            # Запуск мониторинга вывода
            output_thread = threading.Thread(target=self.monitor_output)
            output_thread.daemon = True
            output_thread.start()
            
            return True
        except Exception as e:
            self.log(f"❌ Ошибка запуска бота: {e}")
            return False
    
    def monitor_output(self):
        """Мониторинг вывода бота"""
        try:
            for line in iter(self.bot_process.stdout.readline, ''):
                if line:
                    # Фильтрация важных сообщений
                    line = line.strip()
                    if any(keyword in line.lower() for keyword in 
                           ['error', 'exception', 'connected', 'synced', 'starting']):
                        self.log(f"BOT: {line}")
        except Exception as e:
            self.log(f"Ошибка мониторинга вывода: {e}")
    
    def is_bot_healthy(self):
        """Комплексная проверка здоровья бота"""
        if not self.bot_process:
            return False, "Процесс не запущен"
        
        # Проверка процесса
        if self.bot_process.poll() is not None:
            return False, "Процесс завершен"
        
        # Проверка HTTP сервера
        try:
            response = requests.get("http://localhost:8080/health", timeout=10)
            if response.status_code == 200:
                return True, "Все системы работают"
            else:
                return False, f"HTTP статус {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"HTTP недоступен: {e}"
    
    def stop_bot(self):
        """Остановка бота"""
        if self.bot_process:
            self.log("🛑 Остановка бота...")
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.log("⚠️ Принудительная остановка бота...")
                self.bot_process.kill()
                self.bot_process.wait()
            self.bot_process = None
            self.log("✅ Бот остановлен")
    
    def restart_bot(self):
        """Перезапуск бота"""
        self.restart_count += 1
        self.last_restart = datetime.now()
        
        self.log(f"🔄 Перезапуск бота #{self.restart_count}")
        
        self.stop_bot()
        time.sleep(10)  # Пауза для очистки ресурсов
        
        if self.start_bot():
            self.log("✅ Бот успешно перезапущен")
        else:
            self.log("❌ Ошибка перезапуска бота")
            
        self.save_status()
    
    def cleanup_logs(self):
        """Очистка старых логов"""
        try:
            if self.log_file.exists():
                file_size = self.log_file.stat().st_size
                if file_size > 10 * 1024 * 1024:  # 10MB
                    # Сохранить только последние 5MB
                    with open(self.log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    # Оставить последние 1000 строк
                    with open(self.log_file, "w", encoding="utf-8") as f:
                        f.writelines(lines[-1000:])
                    
                    self.log("🧹 Очищены старые логи")
        except Exception as e:
            self.log(f"Ошибка очистки логов: {e}")
    
    def run(self):
        """Основной цикл мониторинга"""
        self.log("🎯 Запуск постоянного хоста Discord бота")
        self.log("🔧 Система обеспечивает непрерывную работу 24/7")
        
        # Запуск бота
        if not self.start_bot():
            self.log("❌ Не удалось запустить бота")
            return
        
        check_interval = 30  # секунд
        last_cleanup = datetime.now()
        
        # Цикл мониторинга
        while self.should_run:
            try:
                time.sleep(check_interval)
                
                # Проверка здоровья
                is_healthy, status_message = self.is_bot_healthy()
                
                if not is_healthy:
                    self.log(f"⚠️ Бот нездоров: {status_message}")
                    self.restart_bot()
                else:
                    # Периодический отчет о работе
                    uptime = datetime.now() - self.last_restart
                    if uptime.total_seconds() % 3600 < check_interval:  # Каждый час
                        self.log(f"💚 Бот работает стабильно (время работы: {uptime}, перезапусков: {self.restart_count})")
                
                # Очистка логов раз в день
                if datetime.now() - last_cleanup > timedelta(days=1):
                    self.cleanup_logs()
                    last_cleanup = datetime.now()
                
            except KeyboardInterrupt:
                self.log("🛑 Получен сигнал завершения")
                self.should_run = False
            except Exception as e:
                self.log(f"❌ Ошибка в цикле мониторинга: {e}")
                time.sleep(30)
        
        self.stop_bot()
        self.log("🏁 Постоянный хост остановлен")
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        self.log(f"📡 Получен сигнал {signum}")
        self.should_run = False

def main():
    # Создание постоянного хоста
    host = PermanentBotHost()
    
    # Установка обработчиков сигналов
    signal.signal(signal.SIGTERM, host.signal_handler)
    signal.signal(signal.SIGINT, host.signal_handler)
    
    try:
        host.run()
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
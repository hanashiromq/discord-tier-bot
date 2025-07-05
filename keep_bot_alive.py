#!/usr/bin/env python3
"""
Скрипт для поддержания бота в рабочем состоянии
Автоматически перезапускает бота в случае сбоя
"""

import subprocess
import time
import os
import sys
import signal
import threading
from datetime import datetime
import requests

class BotKeeper:
    def __init__(self):
        self.bot_process = None
        self.should_run = True
        self.restart_count = 0
        self.last_restart = datetime.now()
        
    def log(self, message):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def start_bot(self):
        """Запуск бота"""
        try:
            self.log("Запуск Discord бота...")
            self.bot_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.log(f"Бот запущен с PID: {self.bot_process.pid}")
            
            # Запуск мониторинга вывода в отдельном потоке
            output_thread = threading.Thread(target=self.monitor_output)
            output_thread.daemon = True
            output_thread.start()
            
            return True
        except Exception as e:
            self.log(f"Ошибка запуска бота: {e}")
            return False
    
    def monitor_output(self):
        """Мониторинг вывода бота"""
        try:
            for line in iter(self.bot_process.stdout.readline, ''):
                if line:
                    print(line.strip())
        except Exception as e:
            self.log(f"Ошибка мониторинга вывода: {e}")
    
    def is_bot_running(self):
        """Проверка, работает ли бот"""
        if not self.bot_process:
            return False
        
        # Проверка процесса
        if self.bot_process.poll() is not None:
            return False
        
        # Дополнительная проверка через HTTP
        try:
            response = requests.get("http://localhost:8080/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def stop_bot(self):
        """Остановка бота"""
        if self.bot_process:
            self.log("Остановка бота...")
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.log("Принудительная остановка бота...")
                self.bot_process.kill()
                self.bot_process.wait()
            self.bot_process = None
            self.log("Бот остановлен")
    
    def restart_bot(self):
        """Перезапуск бота"""
        self.restart_count += 1
        self.last_restart = datetime.now()
        
        self.log(f"Перезапуск бота #{self.restart_count}")
        
        self.stop_bot()
        time.sleep(5)  # Пауза перед перезапуском
        
        if self.start_bot():
            self.log("Бот успешно перезапущен")
        else:
            self.log("Ошибка перезапуска бота")
    
    def run(self):
        """Основной цикл мониторинга"""
        self.log("Запуск системы мониторинга Discord бота")
        
        # Запуск бота
        if not self.start_bot():
            self.log("Не удалось запустить бота")
            return
        
        # Цикл мониторинга
        while self.should_run:
            try:
                time.sleep(30)  # Проверка каждые 30 секунд
                
                if not self.is_bot_running():
                    self.log("Бот не отвечает! Перезапуск...")
                    self.restart_bot()
                else:
                    # Периодический лог о работе
                    if self.restart_count > 0:
                        self.log(f"Бот работает стабильно (перезапусков: {self.restart_count})")
                    else:
                        self.log("Бот работает стабильно")
                
            except KeyboardInterrupt:
                self.log("Получен сигнал завершения")
                self.should_run = False
            except Exception as e:
                self.log(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(10)
        
        self.stop_bot()
        self.log("Система мониторинга остановлена")
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        self.log(f"Получен сигнал {signum}")
        self.should_run = False

def main():
    keeper = BotKeeper()
    
    # Установка обработчиков сигналов
    signal.signal(signal.SIGTERM, keeper.signal_handler)
    signal.signal(signal.SIGINT, keeper.signal_handler)
    
    try:
        keeper.run()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
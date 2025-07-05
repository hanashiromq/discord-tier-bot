#!/usr/bin/env python3
"""
Система мониторинга Discord бота
Отслеживает состояние бота и предоставляет веб-интерфейс
"""

from flask import Flask, jsonify, render_template_string
import json
import os
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

app = Flask(__name__)

class BotMonitoring:
    def __init__(self):
        self.status_file = Path("bot_status.json")
        self.log_file = Path("bot_host.log")
        
    def get_bot_status(self):
        """Получение статуса бота"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                    
                # Добавление дополнительной информации
                if status.get('pid'):
                    try:
                        process = psutil.Process(status['pid'])
                        status['cpu_percent'] = process.cpu_percent()
                        status['memory_mb'] = process.memory_info().rss / 1024 / 1024
                        status['process_status'] = process.status()
                    except psutil.NoSuchProcess:
                        status['process_exists'] = False
                        
                return status
            else:
                return {"error": "Файл статуса не найден"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_recent_logs(self, lines=50):
        """Получение последних логов"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                    return log_lines[-lines:] if log_lines else []
            else:
                return ["Файл логов не найден"]
        except Exception as e:
            return [f"Ошибка чтения логов: {e}"]
    
    def get_system_info(self):
        """Получение информации о системе"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "uptime": str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())),
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
        except Exception as e:
            return {"error": str(e)}

monitor = BotMonitoring()

@app.route('/')
def index():
    """Главная страница мониторинга"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Bot Monitoring</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status-good { color: #28a745; }
            .status-bad { color: #dc3545; }
            .status-warning { color: #ffc107; }
            .logs { background: #f8f9fa; padding: 15px; border-radius: 4px; max-height: 400px; overflow-y: auto; }
            .metric { display: inline-block; margin: 10px 20px 10px 0; }
            .header { text-align: center; color: #333; }
            pre { white-space: pre-wrap; font-size: 12px; line-height: 1.4; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🤖 Discord Bot Monitoring Dashboard</h1>
            
            <div class="grid">
                <div class="card">
                    <h2>📊 Статус бота</h2>
                    <div id="bot-status">
                        {{ bot_status_html | safe }}
                    </div>
                </div>
                
                <div class="card">
                    <h2>🖥️ Системная информация</h2>
                    <div id="system-info">
                        {{ system_info_html | safe }}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>📝 Последние логи</h2>
                <div class="logs">
                    <pre>{{ logs | safe }}</pre>
                </div>
            </div>
            
            <div class="card">
                <p><small>Последнее обновление: {{ update_time }}</small></p>
                <p><small>Автообновление каждые 30 секунд</small></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Получение данных
    bot_status = monitor.get_bot_status()
    system_info = monitor.get_system_info()
    logs = monitor.get_recent_logs(100)
    
    # Форматирование статуса бота
    if bot_status.get('running'):
        status_class = "status-good"
        status_text = "✅ Работает"
    else:
        status_class = "status-bad"
        status_text = "❌ Не работает"
    
    bot_status_html = f"""
        <div class="metric"><strong>Статус:</strong> <span class="{status_class}">{status_text}</span></div>
        <div class="metric"><strong>Перезапусков:</strong> {bot_status.get('restart_count', 0)}</div>
        <div class="metric"><strong>PID:</strong> {bot_status.get('pid', 'N/A')}</div>
        <div class="metric"><strong>CPU:</strong> {bot_status.get('cpu_percent', 0):.1f}%</div>
        <div class="metric"><strong>RAM:</strong> {bot_status.get('memory_mb', 0):.1f} MB</div>
        <div class="metric"><strong>Последний запуск:</strong> {bot_status.get('last_restart', 'N/A')[:19] if bot_status.get('last_restart') else 'N/A'}</div>
    """
    
    # Форматирование системной информации
    system_info_html = f"""
        <div class="metric"><strong>CPU:</strong> {system_info.get('cpu_percent', 0):.1f}%</div>
        <div class="metric"><strong>RAM:</strong> {system_info.get('memory_percent', 0):.1f}%</div>
        <div class="metric"><strong>Диск:</strong> {system_info.get('disk_percent', 0):.1f}%</div>
        <div class="metric"><strong>Время работы:</strong> {system_info.get('uptime', 'N/A')}</div>
        <div class="metric"><strong>Python:</strong> {system_info.get('python_version', 'N/A')}</div>
    """
    
    # Форматирование логов
    logs_text = ''.join(logs) if logs else "Логи не найдены"
    
    return render_template_string(
        template,
        bot_status_html=bot_status_html,
        system_info_html=system_info_html,
        logs=logs_text,
        update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/api/status')
def api_status():
    """API статуса бота"""
    return jsonify(monitor.get_bot_status())

@app.route('/api/system')
def api_system():
    """API системной информации"""
    return jsonify(monitor.get_system_info())

@app.route('/api/logs')
def api_logs():
    """API логов"""
    lines = int(request.args.get('lines', 50))
    return jsonify({"logs": monitor.get_recent_logs(lines)})

@app.route('/health')
def health():
    """Health check для внешних мониторингов"""
    bot_status = monitor.get_bot_status()
    if bot_status.get('running'):
        return jsonify({"status": "healthy", "message": "Bot is running"}), 200
    else:
        return jsonify({"status": "unhealthy", "message": "Bot is not running"}), 503

if __name__ == '__main__':
    print("🖥️ Запуск веб-интерфейса мониторинга на http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
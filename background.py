
from flask import Flask, jsonify
import time
import requests
import datetime
import threading

app = Flask('')

# Статистика мониторинга
monitor_stats = {
    'service_name': 'Discord Tier Bot Monitor',
    'status': 'active',
    'last_check': datetime.datetime.now().isoformat(),
    'total_checks': 0,
    'failed_checks': 0,
    'bot_url': 'http://localhost:8080'
}

@app.route('/')
def home():
    return jsonify({
        'message': 'Discord Bot Monitor Service',
        'status': 'running',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/monitor-status')
def monitor_status():
    """Статус самого сервиса мониторинга"""
    return jsonify(monitor_stats)

def check_bot_health():
    """Проверка здоровья основного бота"""
    while True:
        try:
            monitor_stats['total_checks'] += 1
            monitor_stats['last_check'] = datetime.datetime.now().isoformat()
            
            # Проверяем основной бот
            response = requests.get(monitor_stats['bot_url'] + '/status', timeout=10)
            
            if response.status_code == 200:
                print(f"[MONITOR] ✅ Bot health check passed - {datetime.datetime.now()}")
                monitor_stats['status'] = 'bot_healthy'
            else:
                monitor_stats['failed_checks'] += 1
                print(f"[MONITOR] ⚠️ Bot health check failed - Status: {response.status_code}")
                monitor_stats['status'] = 'bot_unhealthy'
                
        except Exception as e:
            monitor_stats['failed_checks'] += 1
            monitor_stats['status'] = 'bot_unreachable'
            print(f"[MONITOR] ❌ Bot unreachable: {e}")
        
        # Ждем 5 минут (300 секунд)
        time.sleep(300)

def run_monitor():
    """Запуск Flask сервера мониторинга"""
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    # Запускаем мониторинг в отдельном потоке
    monitor_thread = threading.Thread(target=check_bot_health)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Запускаем Flask сервер
    print("[MONITOR] Starting Discord Bot Monitor Service...")
    run_monitor()

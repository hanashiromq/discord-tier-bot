from flask import Flask, jsonify
from threading import Thread
import time
import requests
import datetime

app = Flask('')

# Статистика для мониторинга
bot_stats = {
    'status': 'running',
    'start_time': datetime.datetime.now().isoformat(),
    'last_ping': datetime.datetime.now().isoformat(),
    'uptime_checks': 0
}

@app.route('/')
def home():
    return "I'm alive"

@app.route('/status')
def status():
    """Эндпоинт для мониторинга статуса бота"""
    bot_stats['last_ping'] = datetime.datetime.now().isoformat()
    bot_stats['uptime_checks'] += 1
    return jsonify(bot_stats)

@app.route('/health')
def health():
    """Эндпоинт для проверки здоровья"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'discord-tier-bot'
    })

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

def ping_server():
    """Keep the server alive by pinging it every 5 minutes"""
    while True:
        try:
            response = requests.get("http://localhost:8080/status", timeout=10)
            if response.status_code == 200:
                print(f"[MONITOR] Bot alive - {datetime.datetime.now()}")
            else:
                print(f"[MONITOR] Warning - Status code: {response.status_code}")
        except Exception as e:
            print(f"[MONITOR] Error pinging server: {e}")
        time.sleep(300)  # Wait 5 minutes

if __name__ == "__main__":
    keep_alive()
    ping_server()
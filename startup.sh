#!/bin/bash

# Скрипт автозапуска Discord бота
# Обеспечивает запуск бота при старте системы

echo "🚀 Инициализация системы постоянного хостинга Discord бота"

# Установка переменных
export PYTHONUNBUFFERED=1
export DISCORD_BOT_HOME="$(pwd)"

# Создание директории для логов
mkdir -p logs

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a logs/startup.log
}

# Проверка зависимостей
log "📦 Проверка зависимостей..."
python3 -c "import discord, aiosqlite" 2>/dev/null
if [ $? -ne 0 ]; then
    log "⚠️ Установка зависимостей..."
    pip install discord.py aiosqlite requests
fi

# Проверка токена
if [ ! -f "token.txt" ]; then
    log "❌ Файл token.txt не найден!"
    echo "Создайте файл token.txt с вашим Discord токеном"
    exit 1
fi

# Проверка длины токена
TOKEN_LENGTH=$(wc -c < token.txt)
if [ $TOKEN_LENGTH -lt 50 ]; then
    log "❌ Токен в token.txt слишком короткий!"
    exit 1
fi

log "✅ Все проверки пройдены"

# Запуск постоянного хоста
log "🎯 Запуск постоянного хоста..."
python3 run_forever.py

log "🏁 Система завершена"
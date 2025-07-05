# Настройка GitHub для Discord Tier Bot

## Шаги для размещения на GitHub

### 1. Подготовка файлов
Все файлы уже готовы для GitHub:
- `.gitignore` - исключает секретные файлы и временные данные
- `LICENSE` - лицензия MIT
- `README.md` - обновленная документация
- `setup_requirements.txt` - список зависимостей
- `token_example.txt` - пример файла токена

### 2. Создание репозитория на GitHub
1. Перейдите на https://github.com
2. Нажмите "New repository"
3. Введите название: `discord-tier-bot`
4. Выберите "Public" или "Private"
5. НЕ добавляйте README, .gitignore или LICENSE (они уже созданы)
6. Нажмите "Create repository"

### 3. Загрузка кода
Выполните команды в терминале:

```bash
# Инициализация git
git init

# Добавление файлов
git add .

# Первый коммит
git commit -m "Initial commit: Discord Tier Bot with 24/7 hosting"

# Подключение к GitHub (замените на ваш репозиторий)
git remote add origin https://github.com/yourusername/discord-tier-bot.git

# Загрузка кода
git push -u origin main
```

### 4. Настройка для других пользователей
После клонирования репозитория пользователи должны:

1. Создать файл `token.txt` с Discord токеном
2. Установить зависимости: `pip install -r setup_requirements.txt`
3. Запустить бота: `python3 main.py`

### 5. Важные файлы для исключения
Эти файлы НЕ попадут в GitHub (указаны в .gitignore):
- `token.txt` - секретный токен
- `tier_bot.db` - база данных
- `*.log` - файлы логов
- `bot_status.json` - статус бота

### 6. Рекомендации по безопасности
- Никогда не коммитьте файл `token.txt`
- Используйте переменные окружения для продакшена
- Регулярно обновляйте зависимости
- Делайте резервные копии базы данных

### 7. Файлы проекта
```
discord-tier-bot/
├── main.py                 # Основной бот
├── run_forever.py          # Постоянный хостинг
├── monitoring.py           # Веб-мониторинг
├── bot_commands.py         # Команды Discord
├── database.py             # Работа с БД
├── views_persistent.py     # UI компоненты
├── config.py               # Конфигурация
├── models.py               # Модели данных
├── status_check.py         # Проверка статуса
├── startup.sh              # Скрипт запуска
├── token_example.txt       # Пример токена
├── setup_requirements.txt  # Зависимости
├── README.md               # Документация
├── LICENSE                 # Лицензия
├── .gitignore              # Исключения Git
└── GITHUB_SETUP.md         # Эта инструкция
```

### 8. Команды для работы с GitHub
```bash
# Клонирование
git clone https://github.com/yourusername/discord-tier-bot.git

# Обновление
git pull origin main

# Добавление изменений
git add .
git commit -m "Описание изменений"
git push origin main

# Просмотр статуса
git status

# Просмотр истории
git log --oneline
```

Ваш Discord бот готов к размещению на GitHub! 🚀
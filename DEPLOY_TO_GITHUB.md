# 🚀 Размещение Discord Tier Bot на GitHub

## Готовые файлы для GitHub

Все файлы подготовлены для размещения на GitHub:

### ✅ Что уже сделано:
- **`.gitignore`** - исключает секретные файлы (token.txt, логи, БД)
- **`LICENSE`** - лицензия MIT
- **`README.md`** - полная документация проекта
- **`setup_requirements.txt`** - список зависимостей Python
- **`token_example.txt`** - пример файла токена
- **`GITHUB_SETUP.md`** - подробная инструкция по настройке

### 📁 Структура проекта для GitHub:
```
discord-tier-bot/
├── main.py                 # Основной файл бота
├── run_forever.py          # Система постоянного хостинга
├── monitoring.py           # Веб-мониторинг на порту 8080
├── bot_commands.py         # Все Discord команды
├── database.py             # Работа с SQLite базой данных
├── database_pg.py          # PostgreSQL версия (опционально)
├── views_persistent.py     # UI компоненты и кнопки
├── config.py               # Конфигурация и настройки
├── models.py               # Модели данных
├── status_check.py         # Проверка статуса системы
├── startup.sh              # Скрипт автозапуска
├── keep_bot_alive.py       # Альтернативный keeper
├── keep_alive.py           # Flask keep-alive сервер
├── background.py           # Фоновые процессы
├── start_monitor.py        # Запуск мониторинга
├── token_example.txt       # Пример токена (НЕ настоящий)
├── setup_requirements.txt  # Зависимости для установки
├── README.md               # Полная документация
├── LICENSE                 # Лицензия MIT
├── .gitignore              # Исключения Git
├── GITHUB_SETUP.md         # Инструкция по настройке
└── DEPLOY_TO_GITHUB.md     # Этот файл
```

## 📋 Пошаговая инструкция

### 1. Создание репозитория на GitHub
1. Перейдите на https://github.com
2. Нажмите **"New repository"**
3. Название: `discord-tier-bot`
4. Описание: `Discord bot for tier management with 24/7 hosting`
5. Выберите **Public** или **Private**
6. НЕ добавляйте README, .gitignore или LICENSE
7. Нажмите **"Create repository"**

### 2. Загрузка файлов (выберите один способ)

#### Способ A: Через веб-интерфейс GitHub
1. В новом репозитории нажмите **"uploading an existing file"**
2. Перетащите все файлы проекта (кроме секретных)
3. Напишите commit message: `Initial commit: Discord Tier Bot`
4. Нажмите **"Commit changes"**

#### Способ B: Через Git командную строку
```bash
git init
git add .
git commit -m "Initial commit: Discord Tier Bot with 24/7 hosting"
git remote add origin https://github.com/ВАШЕ_ИМЯ/discord-tier-bot.git
git push -u origin main
```

### 3. Настройка для других пользователей

После клонирования репозитория другие пользователи должны:

```bash
# Клонирование
git clone https://github.com/ВАШЕ_ИМЯ/discord-tier-bot.git
cd discord-tier-bot

# Установка зависимостей
pip install -r setup_requirements.txt

# Создание файла с токеном
cp token_example.txt token.txt
# Затем отредактировать token.txt и вставить настоящий токен

# Запуск бота
python3 main.py
```

### 4. Безопасность

#### ⚠️ Файлы, которые НЕ попадут в GitHub:
- `token.txt` - секретный токен Discord
- `tier_bot.db` - база данных
- `*.log` - файлы логов
- `bot_status.json` - статус бота
- `__pycache__/` - кэш Python

#### ✅ Рекомендации:
- Никогда не коммитьте настоящий токен
- Используйте переменные окружения для продакшена
- Регулярно обновляйте зависимости
- Делайте резервные копии базы данных

### 5. Возможности бота

#### 🎮 Основные функции:
- **Система тиров T1-T5** с цветовой кодировкой
- **Автоматические заявки** через Discord интерфейс
- **Административные команды** для управления
- **Веб-мониторинг** на http://localhost:8080
- **Постоянный хостинг** с автоматическим перезапуском
- **База данных** для сохранения всех данных
- **Система ролей** для контроля доступа

#### 📊 Команды Discord:
- `/tier_button` - создать кнопку для заявок
- `/tier_top` - топ игроков по тирам
- `/my_tier` - проверить свой тир
- `/player_info` - информация об игроке
- `/setup_roles` - настроить роли
- `/setup_tierlist` - настроить список тиров

### 6. Поддержка

После размещения на GitHub:
- Другие пользователи смогут скачать и запустить бота
- Можно создавать Issues для багов
- Можно принимать Pull Requests с улучшениями
- Документация поможет новым пользователям

## 🎯 Готово к размещению!

Все файлы подготовлены и готовы к загрузке на GitHub. Следуйте инструкциям выше для создания репозитория.
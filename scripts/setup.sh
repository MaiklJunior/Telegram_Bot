#!/bin/bash

# Скрипт первоначальной настройки проекта
# Использование: ./scripts/setup.sh

set -e

echo "🚀 Начинаю настройку Telegram Media Downloader Bot..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Пожалуйста, установите Python 3.9+"
    exit 1
fi

# Проверяем версию Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Требуется Python $REQUIRED_VERSION+, установлена версия $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION найден"

# Создаем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активирую виртуальное окружение..."
source venv/bin/activate

# Обновляем pip
echo "⬆️ Обновляю pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "📚 Устанавливаю зависимости..."
pip install -r requirements.txt

# Создаем .env файл если его нет
if [ ! -f ".env" ]; then
    echo "📝 Создаю .env файл..."
    cp .env.example .env
    echo "⚠️  Пожалуйста, отредактируйте .env файл и добавьте TELEGRAM_BOT_TOKEN"
fi

# Создаем необходимые директории
echo "📁 Создаю директории..."
mkdir -p logs downloads temp

# Делаем скрипт исполняемым
chmod +x run_bot.py

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте .env файл и добавьте TELEGRAM_BOT_TOKEN"
echo "2. Запустите бота: python run_bot.py"
echo "3. Или для развертывания: cd serverless && serverless deploy"
echo ""
echo "📖 Дополнительная информация в README.md"

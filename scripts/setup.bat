@echo off
REM Скрипт первоначальной настройки проекта для Windows
REM Использование: scripts\setup.bat

echo 🚀 Начинаю настройку Telegram Media Downloader Bot...

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Пожалуйста, установите Python 3.9+
    pause
    exit /b 1
)

echo ✅ Python найден

REM Создаем виртуальное окружение
if not exist "venv" (
    echo 📦 Создаю виртуальное окружение...
    python -m venv venv
)

REM Активируем виртуальное окружение
echo 🔧 Активирую виртуальное окружение...
call venv\Scripts\activate.bat

REM Обновляем pip
echo ⬆️ Обновляю pip...
python -m pip install --upgrade pip

REM Устанавливаем зависимости
echo 📚 Устанавливаю зависимости...
pip install -r requirements.txt

REM Создаем .env файл если его нет
if not exist ".env" (
    echo 📝 Создаю .env файл...
    copy .env.example .env
    echo ⚠️ Пожалуйста, отредактируйте .env файл и добавьте TELEGRAM_BOT_TOKEN
)

REM Создаем необходимые директории
echo 📁 Создаю директории...
if not exist "logs" mkdir logs
if not exist "downloads" mkdir downloads
if not exist "temp" mkdir temp

echo.
echo 🎉 Настройка завершена!
echo.
echo 📋 Следующие шаги:
echo 1. Отредактируйте .env файл и добавьте TELEGRAM_BOT_TOKEN
echo 2. Запустите бота: python run_bot.py
echo 3. Или для развертывания: cd serverless ^&^& serverless deploy
echo.
echo 📖 Дополнительная информация в README.md
pause

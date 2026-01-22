@echo off
echo 🚀 Настройка Railway для Telegram Bot
echo.

echo 📋 1. Установка Railway CLI...
npm install -g @railway/cli

echo.
echo 🔐 2. Вход в Railway...
railway login

echo.
echo 📦 3. Создание нового проекта...
railway new

echo.
echo ⬆️ 4. Загрузка кода...
railway up

echo.
echo ✅ 5. Развертывание...
railway deploy

echo.
echo 🎯 Готово! Теперь:
echo 1. Зайдите в Railway Dashboard
echo 2. Скопируйте URL проекта
echo 3. Установите webhook:
echo.
echo curl -X POST "https://api.telegram.org/bot8449129663:AAEHFLl66qDVNB2YXmGh3zvYpo88OisTJ5Y/setWebhook" -H "Content-Type: application/json" -d "{\"url\": \"ВАШ_URL/webhook\", \"drop_pending_updates\": true}"
echo.

pause

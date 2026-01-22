@echo off
echo Установка Webhook для Telegram бота
echo.

echo Замените ВАШ_ТОКЕН на реальный токен от @BotFather
echo.

set /p TOKEN="Введите ваш Telegram Bot Token: "
echo.

echo Устанавливаю webhook...
curl -X POST "https://api.telegram.org/bot%TOKEN%/setWebhook" ^
  -H "Content-Type: application/json" ^
  -d "{\"url\": \"https://telegram-dc7abuxg5-mihails-projects-b1dd402a.vercel.app/api/webhook\", \"drop_pending_updates\": true}"

echo.
echo Проверка статуса webhook...
curl "https://api.telegram.org/bot%TOKEN%/getWebhookInfo"

echo.
echo Готово! Бот должен работать.
pause
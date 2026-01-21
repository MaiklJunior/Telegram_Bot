@echo off
echo 🚀 Развертывание Telegram Media Downloader Bot
echo.

echo Шаг 1: Развертывание на Vercel...
echo.
vercel --prod
echo.

echo ✅ Развертывание завершено!
echo.
echo 🔗 Следующие шаги:
echo 1. Перейдите в Vercel Dashboard: https://vercel.com/dashboard
echo 2. Выберите проект → Settings → Environment Variables
echo 3. Добавьте TELEGRAM_BOT_TOKEN (ваш токен от @BotFather)
echo 4. Сохраните и redeploy проект
echo.
echo 📡 После этого установите webhook:
echo curl -X POST "https://api.telegram.org/botВАШ_ТОКЕН/setWebhook" -H "Content-Type: application/json" -d "{\"url\": \"https://your-project.vercel.app/webhook\", \"drop_pending_updates\": true}"
echo.
echo 🎉 Бот готов к работе!
pause

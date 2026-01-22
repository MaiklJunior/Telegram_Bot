# Скрипт для установки webhook Telegram бота
Write-Host "Установка Webhook для Telegram бота" -ForegroundColor Green
Write-Host ""

# Получаем токен от пользователя
$token = Read-Host "Введите ваш Telegram Bot Token"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "Ошибка: Токен не указан!" -ForegroundColor Red
    exit 1
}

Write-Host "Устанавливаю webhook..." -ForegroundColor Yellow

$webhookUrl = "https://telegram-d8ayc73q7-mihails-projects-b1dd402a.vercel.app/webhook"
$apiUrl = "https://api.telegram.org/bot$token/setWebhook"

$body = @{
    url = $webhookUrl
    drop_pending_updates = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -ContentType "application/json" -Body $body
    
    if ($response.ok) {
        Write-Host "✅ Webhook успешно установлен!" -ForegroundColor Green
        Write-Host "URL: $webhookUrl"
    } else {
        Write-Host "❌ Ошибка при установке webhook" -ForegroundColor Red
        Write-Host $response
    }
}
catch {
    Write-Host "❌ Ошибка: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Проверка статуса webhook..." -ForegroundColor Yellow

try {
    $statusResponse = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getWebhookInfo"
    Write-Host "Статус webhook:" -ForegroundColor Cyan
    $statusResponse | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "❌ Ошибка при проверке статуса: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Готово! Бот должен работать." -ForegroundColor Green
Read-Host "Нажмите Enter для выхода"

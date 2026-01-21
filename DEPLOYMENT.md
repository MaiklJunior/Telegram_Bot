# 🚀 Развертывание Telegram Media Downloader Bot

## 📋 Варианты развертывания

### 1. AWS Lambda (Рекомендуемый)

#### Установка AWS CLI:
```bash
# Windows
winget install Amazon.AWSCLI

# Linux/Mac
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

#### Настройка AWS:
```bash
aws configure
# Введите:
# AWS Access Key ID: ваш_ключ
# AWS Secret Access Key: ваш_секретный_ключ
# Default region name: us-east-1
# Default output format: json
```

#### Развертывание:
```bash
cd serverless
serverless deploy --stage production
```

### 2. Yandex Cloud Functions (Бесплатный вариант)

#### Установка Yandex Cloud CLI:
```bash
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
exec -l $SHELL
```

#### Настройка Yandex Cloud:
```bash
yc init
# Следуйте инструкциям для аутентификации

# Создайте сервисный аккаунт
yc iam service-account create --name telegram-bot

# Назначьте права
yc resource-manager folder add-access-binding <folder-id> \
  --role editor \
  --service-account-name telegram-bot

# Создайте API ключ
yc iam api-key create --service-account-name telegram-bot
```

#### Развертывание:
```bash
cd serverless
npm install serverless-yandex-cloud
serverless deploy --config yandex.yml
```

### 3. Vercel (Самый простой вариант)

#### Установка Vercel CLI:
```bash
npm install -g vercel
```

#### Развертывание:
```bash
# Из корня проекта
vercel --prod
```

### 4. Railway (Простой и дешевый)

#### Развертывание:
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

## 🔧 Настройка Webhook

После развертывания установите webhook:

### AWS Lambda:
```bash
# Получите URL функции
serverless info --stage production

# Установите webhook
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"YOUR_FUNCTION_URL/webhook\", \"drop_pending_updates\": true}"
```

### Vercel:
```bash
# URL будет: https://your-project.vercel.app/webhook
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://your-project.vercel.app/webhook\", \"drop_pending_updates\": true}"
```

## 🎯 Быстрый старт с Vercel (Рекомендую для начала)

1. **Установите Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Авторизуйтесь:**
   ```bash
   vercel login
   ```

3. **Разверните:**
   ```bash
   vercel --prod
   ```

4. **Настройте переменные окружения в Vercel:**
   - Перейдите в dashboard.vercel.com
   - Выберите проект → Settings → Environment Variables
   - Добавьте `TELEGRAM_BOT_TOKEN`

5. **Установите webhook:**
   ```bash
   curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"https://your-project.vercel.app/webhook\", \"drop_pending_updates\": true}"
   ```

## 🔍 Проверка развертывания

### Проверка webhook:
```bash
curl "https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo"
```

### Тестирование:
```bash
# Отправьте тестовое сообщение боту
# Проверьте логи в панели управления платформы
```

## 📊 Мониторинг

### AWS CloudWatch:
- Автоматически настраивается при развертывании
- Логи доступны в AWS Console → CloudWatch → Log groups

### Yandex Cloud Monitoring:
- Логи в Yandex Cloud Console → Logging
- Метрики в Monitoring

### Vercel:
- Логи в Vercel Dashboard → Functions → Logs

## 🔄 Автоматическое обновление

### GitHub Actions:
1. Добавьте секреты в репозиторий:
   - `TELEGRAM_BOT_TOKEN`
   - `AWS_ACCESS_KEY_ID` (для AWS)
   - `AWS_SECRET_ACCESS_KEY` (для AWS)

2. Сделайте push в main ветку - автоматическое развертывание начнется

## ⚠️ Важные замечания

1. **Бесплатные лимиты:**
   - AWS Lambda: 1 млн запросов/месяц бесплатно
   - Vercel: 100GB bandwidth/месяц бесплатно
   - Yandex Cloud: 1 млн вызовов/месяц бесплатно

2. **Безопасность:**
   - Никогда не храните токены в коде
   - Используйте переменные окружения
   - Ограничьте права доступа

3. **Масштабирование:**
   - Все платформы автоматически масштабируются
   - Бот выдержит высокую нагрузку

## 🆘 Поддержка

Если возникли проблемы:
1. Проверьте логи в панели управления
2. Убедитесь что webhook настроен правильно
3. Проверьте переменные окружения
4. Создайте Issue в GitHub репозитории

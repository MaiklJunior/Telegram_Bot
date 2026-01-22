from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Токен Telegram бота
    telegram_bot_token: str
    
    # Настройки логирования
    log_level: str = "INFO"
    
    # URL для webhook (будет установлен при развертывании)
    webhook_url: Optional[str] = None
    
    # Настройки для скачивания
    max_file_size_mb: int = 50
    timeout_seconds: int = 30
    
    # Настройки прокси (если необходимо)
    proxy_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Глобальный экземпляр настроек
try:
    settings = Settings()
except Exception as e:
    print(f"Error loading settings: {e}")
    # Для Vercel используем переменные окружения
    import os
    class FallbackSettings:
        telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        webhook_url = os.getenv('WEBHOOK_URL')
        max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
        timeout_seconds = int(os.getenv('TIMEOUT_SECONDS', '30'))
        proxy_url = os.getenv('PROXY_URL')
    
    settings = FallbackSettings()

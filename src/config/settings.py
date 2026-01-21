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
settings = Settings()

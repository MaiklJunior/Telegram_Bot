#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота
Использование: python run_bot.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем путь к src
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from bot.main import main
from loguru import logger


def check_environment():
    """Проверка наличия необходимых переменных окружения"""
    required_vars = ["TELEGRAM_BOT_TOKEN"]
    
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"Отсутствует переменная окружения: {var}")
            logger.error("Создайте .env файл на основе .env.example")
            return False
    
    return True


def create_directories():
    """Создание необходимых директорий"""
    directories = ["logs", "downloads", "temp"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Директория {directory} создана или уже существует")


def main_run():
    """Основная функция запуска"""
    logger.info("🚀 Запуск Telegram Media Downloader Bot")
    
    # Проверяем окружение
    if not check_environment():
        sys.exit(1)
    
    # Создаем директории
    create_directories()
    
    # Загружаем переменные окружения из .env
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        # Запускаем бота
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_run()

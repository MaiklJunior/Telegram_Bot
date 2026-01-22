import asyncio
import logging
import os
from contextlib import suppress
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from config.settings import settings
from bot.handlers.commands import router as commands_router
from bot.handlers.media import router as media_router


# Настройка логирования
logger.remove()

# Для serverless среды (Vercel) логируем только в консоль
if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    logger.add(
        lambda msg: print(msg, end=""),
        level=settings.log_level,
        format="{time:HH:mm:ss} | {level} | {message}"
    )
else:
    # Для локальной разработки логируем в файл и консоль
    logger.add(
        "logs/bot.log",
        rotation="10 MB",
        retention="7 days",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level=settings.log_level,
        format="{time:HH:mm:ss} | {level} | {message}"
    )


class TelegramBot:
    """Основной класс Telegram бота"""
    
    def __init__(self):
        self.bot = None
        self.dp = None
    
    async def init_bot(self):
        """Инициализация бота и диспетчера"""
        # Создаем экземпляр бота
        self.bot = Bot(
            token=settings.telegram_bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
            )
        )
        
        # Создаем диспетчер
        self.dp = Dispatcher()
        
        # Включаем роутеры
        self.dp.include_router(commands_router)
        self.dp.include_router(media_router)
        
        logger.info("Бот успешно инициализирован")
    
    async def start_polling(self):
        """Запуск бота в режиме опроса"""
        await self.init_bot()
        
        logger.info("Запуск бота в режиме polling...")
        
        try:
            # Удаляем вебхук если он был установлен
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Запускаем polling
            await self.dp.start_polling(
                self.bot,
                handle_signals=False
            )
            
        except TelegramAPIError as e:
            logger.error(f"Ошибка Telegram API: {e}")
            raise
        except Exception as e:
            logger.error(f"Критическая ошибка при запуске бота: {e}")
            raise
        finally:
            if self.bot:
                await self.bot.session.close()
    
    async def setup_webhook(self):
        """Настройка webhook для serverless развертывания"""
        await self.init_bot()
        
        webhook_url = settings.webhook_url
        if not webhook_url:
            raise ValueError("WEBHOOK_URL не указан в настройках")
        
        logger.info(f"Установка webhook: {webhook_url}")
        
        try:
            # Устанавливаем webhook
            await self.bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            
            logger.info("Webhook успешно установлен")
            
        except TelegramAPIError as e:
            logger.error(f"Ошибка при установке webhook: {e}")
            raise
    
    async def handle_webhook_update(self, update_data: dict):
        """Обработка входящего обновления от webhook"""
        if not self.dp:
            await self.init_bot()
        
        try:
            # Создаем объект обновления
            from aiogram.types import Update
            update = Update.model_validate(update_data, context={"bot": self.bot})
            
            # Обрабатываем обновление
            await self.dp.feed_update(self.bot, update)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке webhook обновления: {e}")
            raise


# Глобальный экземпляр бота
bot_instance = TelegramBot()


async def main():
    """Основная функция для запуска бота"""
    try:
        await bot_instance.start_polling()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Бот остановлен из-за ошибки: {e}")
    finally:
        logger.info("Работа бота завершена")


if __name__ == "__main__":
    asyncio.run(main())

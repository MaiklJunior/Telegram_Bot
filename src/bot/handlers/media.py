import re
import asyncio
from typing import Optional
from aiogram import Router, types, F
from aiogram.types import Message, BufferedInputFile
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from ...services.media_downloader import MediaDownloader
from ...config.settings import settings

# Создаем роутер для обработки медиа
router = Router()

# Регулярные выражения для определения платформ
PINTEREST_PATTERN = re.compile(r'https?://(www\.)?(pinterest\.com|pin\.it)/.+')
TIKTOK_PATTERN = re.compile(r'https?://(www\.)?tiktok\.com/@.+')
INSTAGRAM_PATTERN = re.compile(r'https?://(www\.)?(instagram\.com|instagr\.am)/.+')

# Словарь для отслеживания состояния загрузки
loading_states = {}


def is_valid_url(url: str) -> bool:
    """Проверяет, является ли URL валидным и поддерживаемым"""
    url = url.strip()
    
    return (
        PINTEREST_PATTERN.match(url) or
        TIKTOK_PATTERN.match(url) or
        INSTAGRAM_PATTERN.match(url)
    )


def get_platform_name(url: str) -> str:
    """Определяет название платформы по URL"""
    if PINTEREST_PATTERN.match(url):
        return "Pinterest"
    elif TIKTOK_PATTERN.match(url):
        return "TikTok"
    elif INSTAGRAM_PATTERN.match(url):
        return "Instagram"
    else:
        return "Неизвестная платформа"


@router.message(F.text & ~F.command)
async def handle_media_link(message: Message):
    """Обработчик ссылок на медиа"""
    url = message.text.strip()
    user_id = message.from_user.id
    
    # Проверяем, не загружает ли пользователь что-то уже
    if loading_states.get(user_id, False):
        await message.answer(
            "⏳ Пожалуйста, подождите! Ваша предыдущая загрузка еще не завершена."
        )
        return
    
    # Проверяем валидность URL
    if not is_valid_url(url):
        await message.answer(
            "❌ Неверная ссылка! Пожалуйста, отправьте ссылку на:\n"
            "• Pinterest\n"
            "• TikTok\n"
            "• Instagram\n\n"
            "Пример: https://pinterest.com/pin/123456789/"
        )
        return
    
    platform = get_platform_name(url)
    
    # Отправляем сообщение о начале загрузки
    loading_message = await message.answer(
        f"🔍 Определяю платформу: {platform}\n"
        f"⬇️ Начинаю загрузку медиа...\n"
        f"⏳ Это может занять некоторое время..."
    )
    
    # Устанавливаем флаг загрузки
    loading_states[user_id] = True
    
    try:
        # Скачиваем медиа
        async with MediaDownloader() as downloader:
            media_data, file_type = await downloader.download_media(url)
            
            if not media_data:
                await loading_message.edit_text(
                    f"❌ Не удалось скачать медиа с {platform}\n\n"
                    f"Возможные причины:\n"
                    f"• Медиа удалено или недоступно\n"
                    f"• Приватный профиль\n"
                    f"• Временные проблемы с платформой\n\n"
                    f"Попробуйте другую ссылку."
                )
                return
            
            # Проверяем размер файла
            file_size_mb = len(media_data) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                await loading_message.edit_text(
                    f"❌ Файл слишком большой ({file_size_mb:.1f}MB)\n"
                    f"Максимальный размер: {settings.max_file_size_mb}MB"
                )
                return
            
            # Определяем имя файла и тип
            if file_type == 'video':
                filename = f"{platform}_video_{user_id}.mp4"
                caption = f"🎥 Видео из {platform}\n"
            else:
                filename = f"{platform}_photo_{user_id}.jpg"
                caption = f"📸 Фото из {platform}\n"
            
            caption += f"📊 Размер: {file_size_mb:.1f}MB\n"
            caption += f"✅ Качество: Максимальное доступное"
            
            # Создаем файл для отправки
            input_file = BufferedInputFile(
                file=media_data,
                filename=filename
            )
            
            # Отправляем файл
            await loading_message.edit_text("📤 Отправляю файл...")
            
            if file_type == 'video':
                await message.answer_video(
                    video=input_file,
                    caption=caption
                )
            else:
                await message.answer_photo(
                    photo=input_file,
                    caption=caption
                )
            
            # Удаляем сообщение о загрузке
            await loading_message.delete()
            
            logger.info(f"Успешно отправлен файл пользователю {user_id} с {platform}")
            
    except asyncio.TimeoutError:
        await loading_message.edit_text(
            f"⏰ Время загрузки истекло (> {settings.timeout_seconds} сек)\n"
            f"Попробуйте еще раз или выберите другой файл."
        )
        
    except TelegramAPIError as e:
        logger.error(f"Ошибка Telegram API: {e}")
        await loading_message.edit_text(
            "❌ Ошибка при отправке файла\n"
            "Попробуйте еще раз через несколько секунд."
        )
        
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        await loading_message.edit_text(
            "❌ Произошла непредвиденная ошибка\n"
            "Попробуйте еще раз или обратитесь к администратору."
        )
        
    finally:
        # Сбрасываем флаг загрузки
        loading_states[user_id] = False


@router.message(F.photo | F.video | F.animation | F.document)
async def handle_other_media(message: Message):
    """Обработчик других типов медиа (не ссылок)"""
    await message.answer(
        "🔗 Пожалуйста, отправьте ссылку на медиа, а не сам файл.\n\n"
        "Я работаю со ссылками из:\n"
        "• Pinterest\n"
        "• TikTok\n"
        "• Instagram\n\n"
        "Просто вставьте ссылку в чат! 🚀"
    )

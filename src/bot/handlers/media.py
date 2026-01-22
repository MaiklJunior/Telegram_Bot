import re
import asyncio
from typing import Optional
from aiogram import Router, types, F
from aiogram.types import Message, BufferedInputFile
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from services.enhanced_downloader import EnhancedMediaDownloader
from config.settings import settings

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
        async with EnhancedMediaDownloader() as downloader:
            result = await downloader.download_media(url)
            
        items = result.get('items', [])
        post_text = result.get('text')
            
        if not items:
            await loading_message.edit_text(
                f"❌ Не удалось скачать медиа с {platform}\n\n"
                f"Попробуйте другую ссылку."
            )
            return
            
        # Удаляем сообщение о загрузке перед отправкой файлов
        await loading_message.delete()
        
        # Инфо о боте для подписи
        bot_info = await message.bot.get_me()
        bot_username = bot_info.username
        
        # Отправляем текст поста, если он есть
        if post_text:
            await message.answer(f"📝 <b>Текст поста:</b>\n\n{post_text}", parse_mode="HTML")
            
        for i, item in enumerate(items):
            media_data = item['data']
            file_type = item['type']
            
            # Проверяем размер файла
            file_size_mb = len(media_data) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                await message.answer(f"⚠️ Файл {i+1} слишком большой ({file_size_mb:.1f}MB) и был пропущен.")
                continue

            # Определяем имя и подпись
            suffix = f"_{i+1}" if len(items) > 1 else ""
            if file_type == 'video':
                filename = f"video_{user_id}{suffix}.mp4"
                caption = f"Рад был помочь! Ваш, @{bot_username}"
            else:
                filename = f"photo_{user_id}{suffix}.jpg"
                caption = f"Рад был помочь! Ваш, @{bot_username}"
            
            # Создаем файл
            input_file = BufferedInputFile(file=media_data, filename=filename)
            
            if file_type == 'video':
                await message.answer_video(video=input_file, caption=caption)
            else:
                # Отправляем как фото
                await message.answer_photo(photo=input_file, caption=caption)
                
                # Отправляем как документ (для ценителей качества)
                doc_file = BufferedInputFile(file=media_data, filename=filename)
                await message.answer_document(
                    document=doc_file,
                    caption="Для ценителей качества — изображение документом!"
                )
        
        # Отправляем сообщение про донат
        await message.answer(
            "👋 Нравится бот? Поддержите его автора донатом и получите в благодарность бонусную подписку!\n\n"
            "<b>Что она даёт:</b>\n"
            "— отключение рекламы;\n"
            "— отсутствие просьб подписаться на «Семейку ботов»;\n"
            "— скачивание медиа без подписей.\n\n"
            "Нажмите /donate, чтобы выбрать удобный способ поддержки.",
            parse_mode="HTML"
        )
        
        logger.info(f"Успешно отправлено {len(items)} файлов пользователю {user_id} с {platform}")
            
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

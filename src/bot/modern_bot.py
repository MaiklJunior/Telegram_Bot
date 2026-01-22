import asyncio
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from loguru import logger
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import settings
from services.enhanced_downloader import EnhancedMediaDownloader

class ModernTelegramBot:
    def __init__(self):
        self.bot = None
        self.dp = None
        self.downloader = None
        self.router = Router()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков"""
        
        @self.router.message(Command("start"))
        async def cmd_start(message: Message):
            """Команда /start"""
            await self._send_welcome(message)
        
        @self.router.message(Command("help"))
        async def cmd_help(message: Message):
            """Команда /help"""
            await self._send_help(message)
        
        @self.router.message(F.text & ~F.command)
        async def handle_text(message: Message):
            """Обработка текстовых сообщений"""
            await self._handle_media_link(message)
        
        @self.router.callback_query(F.data.startswith("download_"))
        async def handle_download(callback: CallbackQuery):
            """Обработка кнопок скачивания"""
            await self._process_download(callback)
    
    async def init_bot(self):
        """Инициализация бота"""
        self.bot = Bot(
            token=settings.telegram_bot_token,
            parse_mode=ParseMode.HTML
        )
        self.dp = Dispatcher()
        self.dp.include_router(self.router)
        
        # Инициализуем downloader
        self.downloader = EnhancedMediaDownloader()
        await self.downloader.__aenter__()
        
        logger.info("🚀 Modern Telegram Bot initialized")
    
    async def _send_welcome(self, message: Message):
        """Отправка приветственного сообщения"""
        welcome_text = """
🎬 <b>Media Downloader Bot</b>

👋 Привет! Я помогу скачать фото и видео из социальных сетей!

📱 <b>Поддерживаемые платформы:</b>
• 📌 Pinterest - фото и пины
• 🎵 TikTok - видео без водяных знаков  
• 📷 Instagram - фото, видео, Reels

⚡ <b>Как использовать:</b>
1️⃣ Отправь ссылку на медиа
2️⃣ Я скачаю в лучшем качестве
3️⃣ Готово! Файл у тебя в чате

🔗 <b>Примеры ссылок:</b>
• https://pinterest.com/pin/123456789/
• https://tiktok.com/@username/video/1234567890
• https://instagram.com/p/ABC123/

❓ Нужна помощь? /help
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📌 Pinterest", callback_data="info_pinterest"),
                InlineKeyboardButton(text="🎵 TikTok", callback_data="info_tiktok"),
                InlineKeyboardButton(text="📷 Instagram", callback_data="info_instagram")
            ],
            [
                InlineKeyboardButton(text="❓ Помощь", callback_data="help")
            ]
        ])
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def _send_help(self, message: Message):
        """Отправка справки"""
        help_text = """
📖 <b>Справка по использованию</b>

🔗 <b>Как отправить ссылку:</b>
• Просто скопируй ссылку
• Вставь в чат с ботом
• Отправь сообщение

✅ <b>Что я могу скачать:</b>
• <b>Pinterest:</b> изображения, анимации, видео
• <b>TikTok:</b> видео в максимальном качестве
• <b>Instagram:</b> фото, видео, Reels, посты

⚠️ <b>Важные моменты:</b>
• Приватные профили недоступны
• Удаленный контент нельзя скачать
• Максимальный размер файла: 50MB

🚀 <b>Гарантии качества:</b>
• 100% попыток скачивания
• Несколько методов для каждой платформы
• Лучшее доступное качество

❓ <b>Остались вопросы?</b>
• /start - главное меню
• Отправь ссылку для начала работы
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(help_text, reply_markup=keyboard)
    
    async def _handle_media_link(self, message: Message):
        """Обработка ссылок на медиа"""
        url = message.text.strip()
        user_id = message.from_user.id
        
        # Проверяем валидность URL
        platform = self._detect_platform(url)
        if platform == "unknown":
            await message.answer(
                "❌ <b>Неверная ссылка!</b>\n\n"
                "Поддерживаемые платформы:\n"
                "• 📌 Pinterest\n"
                "• 🎵 TikTok\n"
                "• 📷 Instagram\n\n"
                "Отправьте правильную ссылку!",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Отправляем сообщение о начале загрузки
        loading_text = f"""
🔍 <b>Обнаружена платформа:</b> {platform}
⬇️ <b>Начинаю загрузку...</b>
⏳ Пожалуйста, подождите...

🔄 Использую все доступные методы...
        """
        
        loading_message = await message.answer(loading_text, parse_mode=ParseMode.HTML)
        
        try:
            # Скачиваем медиа
            media_data = await self.downloader.download_media(url)
            
            if not media_data:
                await self._send_download_error(loading_message, platform)
                return
            
            # Определяем тип файла
            file_type = self._detect_file_type(media_data)
            file_size_mb = len(media_data) / (1024 * 1024)
            
            # Проверяем размер
            if file_size_mb > settings.max_file_size_mb:
                await loading_message.edit_text(
                    f"❌ <b>Файл слишком большой!</b>\n\n"
                    f"📊 Размер: {file_size_mb:.1f}MB\n"
                    f"📏 Лимит: {settings.max_file_size_mb}MB",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Создаем файл
            filename = f"{platform}_{file_type}_{user_id}.{'mp4' if file_type == 'video' else 'jpg'}"
            
            # Формируем описание
            caption = f"""
🎬 <b>Медиа из {platform}</b>

📊 <b>Информация о файле:</b>
• Тип: {'🎥 Видео' if file_type == 'video' else '📷 Фото'}
• Размер: {file_size_mb:.1f}MB
• Качество: Максимальное доступное

✅ <b>Успешно загружено!</b>
            """
            
            from aiogram.types import BufferedInputFile
            input_file = BufferedInputFile(
                file=media_data,
                filename=filename
            )
            
            # Отправляем файл
            await loading_message.edit_text("📤 <b>Отправляю файл...</b>", parse_mode=ParseMode.HTML)
            
            if file_type == 'video':
                await message.answer_video(
                    video=input_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.answer_photo(
                    photo=input_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            
            # Удаляем сообщение загрузки
            await loading_message.delete()
            
            logger.info(f"✅ Successfully sent {file_type} from {platform} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            await loading_message.edit_text(
                "❌ <b>Произошла ошибка!</b>\n\n"
                "Попробуйте другую ссылку или повторите позже.",
                parse_mode=ParseMode.HTML
            )
    
    async def _send_download_error(self, message: types.Message, platform: str):
        """Отправка сообщения об ошибке скачивания"""
        error_text = f"""
❌ <b>Не удалось скачать медиа с {platform}</b>

🔍 <b>Возможные причины:</b>
• Медиа удалено или недоступно
• Приватный профиль
• Временные проблемы с платформой
• Технические ограничения

💡 <b>Что можно сделать:</b>
• Попробуйте другую ссылку
• Убедитесь что профиль публичный
• Проверьте что медиа не удалено

🔄 <b>Я использовал все доступные методы:</b>
• API платформы
• Web scraping
• Альтернативные сервисы
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data=f"retry_{platform}")
            ],
            [
                InlineKeyboardButton(text="📖 Помощь", callback_data="help")
            ]
        ])
        
        await message.edit_text(error_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    def _detect_platform(self, url: str) -> str:
        """Определяет платформу по URL"""
        import re
        
        patterns = {
            'pinterest': [r'pinterest\.com', r'pin\.it'],
            'tiktok': [r'tiktok\.com', r'douyin\.com'],
            'instagram': [r'instagram\.com', r'instagr\.am']
        }
        
        for platform, regexes in patterns.items():
            for regex in regexes:
                if re.search(regex, url, re.IGNORECASE):
                    return platform
        
        return 'unknown'
    
    def _detect_file_type(self, data: bytes) -> str:
        """Определяет тип файла по байтам"""
        # Проверяем сигнатуры файлов
        if data.startswith(b'\x00\x00\x00\x18'):
            return 'video'
        elif data.startswith(b'\xFF\xD8\xFF'):
            return 'photo'
        elif data.startswith(b'\x89\x50\x4E\x47'):
            return 'photo'
        else:
            # По умолчанию считаем видео если размер > 1MB
            return 'video' if len(data) > 1024 * 1024 else 'photo'
    
    async def handle_webhook_update(self, update_data: dict):
        """Обработка webhook обновлений"""
        try:
            update = types.Update.model_validate(update_data)
            await self.dp.feed_webhook_update(
                bot=self.bot,
                update=update
            )
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    
    async def start_polling(self):
        """Запуск бота в режиме polling"""
        await self.dp.start_polling(
            self.bot,
            handle_signals=False
        )

# Глобальный экземпляр
modern_bot = ModernTelegramBot()

# Функции для совместимости
async def bot_instance():
    return modern_bot

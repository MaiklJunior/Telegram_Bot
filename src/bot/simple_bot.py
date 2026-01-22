import asyncio
import aiohttp
import re
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from loguru import logger
import sys
import os
from typing import Optional

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import settings

class SimpleTelegramBot:
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.dp = Dispatcher()
        self.router = Router()
        self.session = None
        self._setup_handlers()
        
        # Включаем роутер в диспетчер
        self.dp.include_router(self.router)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
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
    
    async def _send_welcome(self, message: Message):
        """Отправка приветственного сообщения"""
        text = """
🎬 <b>Simple Media Downloader</b>

📎 <b>Поддерживаемые платформы:</b>
• 📌 Pinterest - фото и видео
• 🎵 TikTok - видео без водяных знаков
• 📷 Instagram - только фото

💡 <b>Как использовать:</b>
1. Отправьте ссылку на медиа
2. Дождитесь загрузки
3. Получите файл

🚀 <b>Начните прямо сейчас!</b>
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📌 Pinterest", callback_data="info_pinterest"),
                InlineKeyboardButton(text="🎵 TikTok", callback_data="info_tiktok"),
                InlineKeyboardButton(text="📷 Instagram", callback_data="info_instagram")
            ],
            [
                InlineKeyboardButton(text="📖 Помощь", callback_data="help")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def _send_help(self, message: Message):
        """Отправка помощи"""
        text = """
📖 <b>Помощь - Simple Media Downloader</b>

🔗 <b>Поддерживаемые ссылки:</b>
• Pinterest: pinterest.com/pin/ID
• TikTok: tiktok.com/@user/video/ID
• Instagram: instagram.com/p/ID (только фото)

⚡ <b>Особенности:</b>
• Автоматическое определение платформы
• Лучшее качество медиа
• Быстрая загрузка
• Простота использования

❓ <b>Вопросы?</b>
Если что-то не работает - попробуйте другую ссылку
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def _handle_media_link(self, message: Message):
        """Обработка ссылок на медиа"""
        url = message.text.strip()
        user_id = message.from_user.id
        
        # Определяем платформу
        platform = self._detect_platform(url)
        
        if platform == 'unknown':
            await message.answer(
                "❌ <b>Неизвестная платформа!</b>\n\n"
                "📎 Поддерживаются: Pinterest, TikTok",
                parse_mode=ParseMode.HTML
            )
            return
        
        if platform == 'instagram':
            await message.answer(
                "📷 <b>Instagram - только фото!</b>\n\n"
                "⚠️ Видео и Reels не поддерживаются\n"
                "📸 Только обычные посты с фото",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Отправляем сообщение о загрузке
        loading_message = await message.answer(
            f"⬇️ <b>Загружаю медиа из {platform.title()}...</b>",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Скачиваем медиа
            media_data, filename, file_type = await self._download_media(url, platform)
            
            if not media_data:
                await loading_message.edit_text(
                    f"❌ <b>Не удалось скачать медиа из {platform.title()}!</b>\n\n"
                    "💡 Попробуйте другую ссылку",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Проверяем размер файла
            file_size_mb = len(media_data) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                await loading_message.edit_text(
                    f"❌ <b>Файл слишком большой!</b>\n\n"
                    f"📊 Размер: {file_size_mb:.1f}MB\n"
                    f"📏 Лимит: {settings.max_file_size_mb}MB",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Отправляем файл
            await loading_message.edit_text("📤 <b>Отправляю файл...</b>", parse_mode=ParseMode.HTML)
            
            from aiogram.types import BufferedInputFile
            input_file = BufferedInputFile(
                file=media_data,
                filename=filename
            )
            
            # Формируем описание
            caption = f"""
🎬 <b>Медиа из {platform.title()}</b>

📊 <b>Информация:</b>
• Тип: {'🎥 Видео' if file_type == 'video' else '📷 Фото'}
• Размер: {file_size_mb:.1f}MB
• Качество: Лучшее

✅ <b>Готово!</b>
            """
            
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
                "❌ <b>Ошибка загрузки!</b>\n\n"
                "💡 Попробуйте другую ссылку",
                parse_mode=ParseMode.HTML
            )
    
    def _detect_platform(self, url: str) -> str:
        """Определяет платформу по URL"""
        url_lower = url.lower()
        
        # Pinterest patterns
        if re.search(r'pinterest\.com|pin\.it', url_lower):
            return 'pinterest'
        
        # TikTok patterns
        if re.search(r'tiktok\.com|douyin\.com', url_lower):
            return 'tiktok'
        
        # Instagram patterns (отключен)
        if re.search(r'instagram\.com/p/|instagram\.com/reel/|instagr\.am/p/', url_lower):
            return 'instagram'
        
        return 'unknown'
    
    async def _download_media(self, url: str, platform: str) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
        """Скачивание медиа"""
        try:
            if platform == 'pinterest':
                return await self._download_pinterest(url)
            elif platform == 'tiktok':
                return await self._download_tiktok(url)
            elif platform == 'instagram':
                return await self._download_instagram(url)
            else:
                return None, None, None
        except Exception as e:
            logger.error(f"Download error for {platform}: {e}")
            return None, None, None
    
    async def _download_pinterest(self, url: str) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
        """Скачать медиа из Pinterest"""
        try:
            logger.info(f"Downloading Pinterest: {url}")
            
            # Извлекаем ID пина
            pin_id_match = re.search(r'pin/(\d+)', url)
            if not pin_id_match:
                return None, None, None
            
            pin_id = pin_id_match.group(1)
            
            # Пробуем разные методы
            methods = [
                self._pinterest_direct,
                self._pinterest_api,
                self._pinterest_scrape
            ]
            
            for method in methods:
                try:
                    result = await method(url, pin_id)
                    if result:
                        return result
                except:
                    continue
            
            return None, None, None
            
        except Exception as e:
            logger.error(f"Pinterest download failed: {e}")
            return None, None, None
    
    async def _pinterest_direct(self, url: str, pin_id: str) -> Optional[tuple]:
        """Прямой метод Pinterest"""
        try:
            # Пробуем прямой URL изображения
            direct_url = f"https://i.pinimg.com/originals/{pin_id}.jpg"
            
            async with self.session.get(direct_url) as response:
                if response.status == 200:
                    data = await response.read()
                    if len(data) > 1024:
                        return data, f"pinterest_{pin_id}.jpg", "image"
        except:
            pass
        return None
    
    async def _pinterest_api(self, url: str, pin_id: str) -> Optional[tuple]:
        """API метод Pinterest"""
        try:
            api_url = f"https://www.pinterest.com/resource/PinResource/get/"
            
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    # Ищем изображения в ответе
                    text = await response.text()
                    img_match = re.search(r'(https://i\.pinimg\.com[^"\s]+\.jpg)', text)
                    if img_match:
                        img_url = img_match.group(1)
                        
                        async with self.session.get(img_url) as img_response:
                            if img_response.status == 200:
                                data = await img_response.read()
                                if len(data) > 1024:
                                    return data, f"pinterest_{pin_id}.jpg", "image"
        except:
            pass
        return None
    
    async def _pinterest_scrape(self, url: str, pin_id: str) -> Optional[tuple]:
        """Scraping метод Pinterest"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Ищем изображения в meta тегах
                    img_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                    if img_match:
                        img_url = img_match.group(1)
                        
                        async with self.session.get(img_url) as img_response:
                            if img_response.status == 200:
                                data = await img_response.read()
                                if len(data) > 1024:
                                    return data, f"pinterest_{pin_id}.jpg", "image"
                    
                    # Ищем видео
                    video_match = re.search(r'<meta property="og:video" content="([^"]+)"', html)
                    if video_match:
                        video_url = video_match.group(1)
                        
                        async with self.session.get(video_url) as video_response:
                            if video_response.status == 200:
                                data = await video_response.read()
                                if len(data) > 1024:
                                    return data, f"pinterest_{pin_id}.mp4", "video"
        except:
            pass
        return None
    
    async def _download_instagram(self, url: str) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
        """Скачать фото из Instagram (только фото, без видео)"""
        try:
            logger.info(f"Downloading Instagram photo: {url}")
            
            # Извлекаем shortcode
            shortcode_match = re.search(r'/p/([^/]+)', url)
            if not shortcode_match:
                return None, None, None
            
            shortcode = shortcode_match.group(1)
            
            # Пробуем разные методы для фото
            methods = [
                self._instagram_direct,
                self._instagram_embed,
                self._instagram_scrape
            ]
            
            for method in methods:
                try:
                    result = await method(url, shortcode)
                    if result:
                        return result
                except:
                    continue
            
            return None, None, None
            
        except Exception as e:
            logger.error(f"Instagram photo download failed: {e}")
            return None, None, None
    
    async def _instagram_direct(self, url: str, shortcode: str) -> Optional[tuple]:
        """Прямой метод Instagram для фото"""
        try:
            # Пробуем прямой URL изображения
            direct_url = f"https://instagram.com/p/{shortcode}/media"
            
            async with self.session.get(direct_url) as response:
                if response.status == 200:
                    data = await response.read()
                    if len(data) > 1024 and not data.startswith(b'<'):
                        return data, f"instagram_{shortcode}.jpg", "image"
        except:
            pass
        return None
    
    async def _instagram_embed(self, url: str, shortcode: str) -> Optional[tuple]:
        """Embed метод Instagram"""
        try:
            embed_url = f"https://www.instagram.com/p/{shortcode}/embed"
            
            async with self.session.get(embed_url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Ищем URL изображения в embed
                    img_match = re.search(r'"display_url":"([^"]+)"', html)
                    if img_match:
                        img_url = img_match.group(1).replace('\\/', '/')
                        
                        async with self.session.get(img_url) as img_response:
                            if img_response.status == 200:
                                data = await img_response.read()
                                if len(data) > 1024:
                                    return data, f"instagram_{shortcode}.jpg", "image"
        except:
            pass
        return None
    
    async def _instagram_scrape(self, url: str, shortcode: str) -> Optional[tuple]:
        """Scraping метод Instagram"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Ищем изображения в meta тегах
                    img_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                    if img_match:
                        img_url = img_match.group(1)
                        
                        async with self.session.get(img_url) as img_response:
                            if img_response.status == 200:
                                data = await img_response.read()
                                if len(data) > 1024:
                                    return data, f"instagram_{shortcode}.jpg", "image"
        except:
            pass
        return None
    
    async def _download_tiktok(self, url: str) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
        """Скачать видео из TikTok"""
        try:
            logger.info(f"Downloading TikTok: {url}")
            
            # Извлекаем ID видео
            video_id_match = re.search(r'/video/(\d+)', url)
            if not video_id_match:
                return None, None, None
            
            video_id = video_id_match.group(1)
            
            # Пробуем разные методы
            methods = [
                self._tiktok_direct,
                self._tiktok_api,
                self._tiktok_alternative
            ]
            
            for method in methods:
                try:
                    result = await method(url, video_id)
                    if result:
                        return result
                except:
                    continue
            
            return None, None, None
            
        except Exception as e:
            logger.error(f"TikTok download failed: {e}")
            return None, None, None
    
    async def _tiktok_direct(self, url: str, video_id: str) -> Optional[tuple]:
        """Прямой метод TikTok"""
        try:
            # Пробуем мобильную версию
            mobile_url = url.replace('tiktok.com', 'vm.tiktok.com')
            
            async with self.session.get(mobile_url) as response:
                if response.status == 200:
                    # Следуем за редиректом
                    final_url = str(response.url)
                    
                    # Ищем видео в странице
                    html = await response.text()
                    video_match = re.search(r'(https://[^"\s]+\.mp4[^"\s]*)', html)
                    if video_match:
                        video_url = video_match.group(1)
                        
                        async with self.session.get(video_url) as video_response:
                            if video_response.status == 200:
                                data = await video_response.read()
                                if len(data) > 1024:
                                    return data, f"tiktok_{video_id}.mp4", "video"
        except:
            pass
        return None
    
    async def _tiktok_api(self, url: str, video_id: str) -> Optional[tuple]:
        """API метод TikTok"""
        try:
            # Пробуем разные API endpoints
            api_urls = [
                f"https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={video_id}",
                f"https://api22-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={video_id}"
            ]
            
            for api_url in api_urls:
                try:
                    headers = {
                        'User-Agent': 'com.zhiliaoapp.musically/2022600040'
                    }
                    
                    async with self.session.get(api_url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            aweme_list = data.get('aweme_list', [])
                            if aweme_list:
                                aweme = aweme_list[0]
                                video = aweme.get('video', {})
                                play_addr = video.get('play_addr', {})
                                url_list = play_addr.get('url_list', [])
                                if url_list:
                                    video_url = url_list[0]
                                    
                                    async with self.session.get(video_url) as video_response:
                                        if video_response.status == 200:
                                            video_data = await video_response.read()
                                            if len(video_data) > 1024:
                                                return video_data, f"tiktok_{video_id}.mp4", "video"
                except:
                    continue
        except:
            pass
        return None
    
    async def _tiktok_alternative(self, url: str, video_id: str) -> Optional[tuple]:
        """Альтернативный метод TikTok"""
        try:
            # Пробуем внешние сервисы
            services = [
                f'https://tikmate.online/download?url={url}',
                f'https://snaptik.app/abc?url={url}'
            ]
            
            for service_url in services:
                try:
                    async with self.session.get(service_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            video_match = re.search(r'(https://[^"\s]+\.mp4[^"\s]*)', html)
                            if video_match:
                                video_url = video_match.group(1)
                                
                                async with self.session.get(video_url) as video_response:
                                    if video_response.status == 200:
                                        data = await video_response.read()
                                        if len(data) > 1024:
                                            return data, f"tiktok_{video_id}.mp4", "video"
                except:
                    continue
        except:
            pass
        return None

# Создаем экземпляр бота
simple_bot = SimpleTelegramBot()

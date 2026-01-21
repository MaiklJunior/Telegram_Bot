import asyncio
import aiohttp
import re
from typing import Optional, Tuple
from urllib.parse import urlparse
from loguru import logger
import yt_dlp
import instaloader
from bs4 import BeautifulSoup


class MediaDownloader:
    """Сервис для скачивания медиа с различных платформ"""
    
    def __init__(self):
        self.session = None
        self.ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def detect_platform(self, url: str) -> str:
        """Определяет платформу по URL"""
        domain = urlparse(url).netloc.lower()
        
        if 'pinterest.com' in domain or 'pin.it' in domain:
            return 'pinterest'
        elif 'tiktok.com' in domain:
            return 'tiktok'
        elif 'instagram.com' in domain or 'instagr.am' in domain:
            return 'instagram'
        else:
            return 'unknown'
    
    async def download_pinterest_media(self, url: str) -> Optional[bytes]:
        """Скачивает медиа с Pinterest"""
        try:
            logger.info(f"Загрузка медиа с Pinterest: {url}")
            
            # Используем yt-dlp для Pinterest
            ydl_opts = self.ydl_opts.copy()
            ydl_opts['format'] = 'best'
            
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        return info.get('url')
                return None
            
            # Выполняем в отдельном потоке чтобы не блокировать event loop
            loop = asyncio.get_event_loop()
            media_url = await loop.run_in_executor(None, download)
            
            if media_url:
                async with self.session.get(media_url) as response:
                    if response.status == 200:
                        return await response.read()
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке с Pinterest: {e}")
            return None
    
    async def download_tiktok_media(self, url: str) -> Optional[bytes]:
        """Скачивает видео с TikTok без водяных знаков"""
        try:
            logger.info(f"Загрузка видео с TikTok: {url}")
            
            # Используем yt-dlp для TikTok (автоматически убирает водяные знаки)
            ydl_opts = self.ydl_opts.copy()
            ydl_opts['format'] = 'best'
            
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        return info.get('url')
                return None
            
            loop = asyncio.get_event_loop()
            media_url = await loop.run_in_executor(None, download)
            
            if media_url:
                async with self.session.get(media_url) as response:
                    if response.status == 200:
                        return await response.read()
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке с TikTok: {e}")
            return None
    
    async def download_instagram_media(self, url: str) -> Optional[bytes]:
        """Скачивает медиа с Instagram"""
        try:
            logger.info(f"Загрузка медиа с Instagram: {url}")
            
            # Используем yt-dlp для Instagram
            ydl_opts = self.ydl_opts.copy()
            ydl_opts['format'] = 'best'
            
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        return info.get('url')
                return None
            
            loop = asyncio.get_event_loop()
            media_url = await loop.run_in_executor(None, download)
            
            if media_url:
                async with self.session.get(media_url) as response:
                    if response.status == 200:
                        return await response.read()
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке с Instagram: {e}")
            return None
    
    async def download_media(self, url: str) -> Tuple[Optional[bytes], str]:
        """Основной метод для скачивания медиа"""
        platform = self.detect_platform(url)
        
        if platform == 'pinterest':
            media_data = await self.download_pinterest_media(url)
            file_type = 'photo' if media_data and len(media_data) < 10 * 1024 * 1024 else 'video'
        elif platform == 'tiktok':
            media_data = await self.download_tiktok_media(url)
            file_type = 'video'
        elif platform == 'instagram':
            media_data = await self.download_instagram_media(url)
            file_type = 'photo' if media_data and len(media_data) < 10 * 1024 * 1024 else 'video'
        else:
            return None, 'unknown'
        
        return media_data, file_type

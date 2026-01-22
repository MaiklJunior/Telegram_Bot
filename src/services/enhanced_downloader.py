import asyncio
import aiohttp
import yt_dlp
import re
from typing import Optional, List
from loguru import logger
from bs4 import BeautifulSoup
import json
from .instagram_api import InstagramAPIDownloader

class EnhancedMediaDownloader:
    def __init__(self):
        self.session = None
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'best',
            'noplaylist': True,
            'extractaudio': False,
            'audioformat': 'best',
            'ignoreerrors': True,
            'no_check_certificate': True,
            'source_address': '0.0.0.0'
        }
        
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
    
    def detect_platform(self, url: str) -> str:
        """Определяет платформу по URL"""
        url_lower = url.lower()
        
        # Pinterest patterns
        if re.search(r'pinterest\.com|pin\.it', url_lower):
            return 'pinterest'
        
        # TikTok patterns (более точные)
        if re.search(r'tiktok\.com|douyin\.com', url_lower):
            return 'tiktok'
        
        # Instagram patterns (более точные)
        if re.search(r'instagram\.com/p/|instagram\.com/reel/|instagram\.com/tv/|instagr\.am/p/', url_lower):
            return 'instagram'
        
        return 'unknown'
    
    async def download_pinterest_media(self, url: str) -> Optional[bytes]:
        """Улучшенное скачивание Pinterest с несколькими методами"""
        
        # Метод 1: Cobalt API (Новый метод)
        result = await self._cobalt_api(url)
        if result:
            return result

        # Метод 2: yt-dlp
        result = await self._pinterest_ytdlp(url)
        if result:
            return result
        
        # Метод 2: Pinterest API
        result = await self._pinterest_api(url)
        if result:
            return result
        
        # Метод 3: Web scraping
        result = await self._pinterest_scrape(url)
        if result:
            return result
        
        logger.error(f"Все методы Pinterest не сработали для: {url}")
        return None
    
    async def _pinterest_ytdlp(self, url: str) -> Optional[bytes]:
        """Метод 1: yt-dlp для Pinterest"""
        try:
            logger.info(f"Pinterest yt-dlp: {url}")
            
            ydl_opts = self.ydl_opts.copy()
            ydl_opts.update({
                'format': 'best',
                'extract_flat': False,
                'ignoreerrors': True
            })
            
            def download():
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if info:
                            # Пробуем разные источники
                            if info.get('url'):
                                return info.get('url')
                            elif info.get('formats'):
                                for fmt in info.get('formats', []):
                                    if fmt.get('url') and fmt.get('ext') in ['mp4', 'jpg', 'png']:
                                        return fmt.get('url')
                            elif info.get('thumbnail'):
                                return info.get('thumbnail')
                except Exception as e:
                    logger.debug(f"yt-dlp Pinterest error: {e}")
                return None
            
            loop = asyncio.get_event_loop()
            media_url = await loop.run_in_executor(None, download)
            
            if media_url and self.session:
                return await self._download_from_url(media_url)
            
        except Exception as e:
            logger.debug(f"Pinterest yt-dlp method failed: {e}")
        return None
    
    async def _pinterest_api(self, url: str) -> Optional[bytes]:
        """Метод 2: Pinterest API эмуляция"""
        try:
            logger.info(f"Pinterest API: {url}")
            
            # Извлекаем ID пина
            pin_id_match = re.search(r'pin/(\d+)', url)
            if not pin_id_match:
                return None
            
            pin_id = pin_id_match.group(1)
            
            # Эмулируем API запрос
            api_url = f"https://www.pinterest.com/resource/PinResource/get/?data={{\"options\":{{\"field_set_key\":\"unauth_react_pin_detail\",\"id\":{pin_id}}},\"context\":{{}}}}"
            
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    pin_data = data.get('resource_response', {}).get('data', {})
                    
                    # Ищем изображения
                    images = pin_data.get('images', {})
                    if images:
                        # Берем самое большое изображение
                        orig_image = images.get('orig', {})
                        if orig_image.get('url'):
                            return await self._download_from_url(orig_image.get('url'))
                    
                    # Ищем видео
                    videos = pin_data.get('videos', {})
                    if videos:
                        video_list = videos.get('video_list', {})
                        if video_list:
                            # Берем видео лучшего качества
                            best_video = max(video_list.values(), key=lambda x: x.get('width', 0) * x.get('height', 0))
                            if best_video.get('url'):
                                return await self._download_from_url(best_video.get('url'))
        
        except Exception as e:
            logger.debug(f"Pinterest API method failed: {e}")
        return None
    
    async def _pinterest_scrape(self, url: str) -> Optional[bytes]:
        """Метод 3: Web scraping"""
        try:
            logger.info(f"Pinterest scraping: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем JSON данные в скриптах
                    scripts = soup.find_all('script', type='application/ld+json')
                    for script in scripts:
                        try:
                            data = json.loads(script.string)
                            if isinstance(data, list):
                                data = data[0]
                            
                            # Ищем изображения
                            if data.get('image'):
                                image_url = data['image']
                                if isinstance(image_url, list):
                                    image_url = image_url[0]
                                return await self._download_from_url(image_url)
                            
                            # Ищем видео
                            if data.get('video'):
                                video_url = data['video']
                                if isinstance(video_url, dict):
                                    video_url = video_url.get('contentUrl')
                                return await self._download_from_url(video_url)
                        except:
                            continue
                    
                    # Ищем в тегах meta
                    meta_image = soup.find('meta', property='og:image')
                    if meta_image and meta_image.get('content'):
                        return await self._download_from_url(meta_image.get('content'))
                    
                    meta_video = soup.find('meta', property='og:video')
                    if meta_video and meta_video.get('content'):
                        return await self._download_from_url(meta_video.get('content'))
        
        except Exception as e:
            logger.debug(f"Pinterest scraping method failed: {e}")
        return None
    
    async def download_tiktok_media(self, url: str) -> Optional[bytes]:
        """Улучшенное скачивание TikTok"""
        
        # Метод 1: Cobalt API (Самый стабильный)
        result = await self._cobalt_api(url)
        if result:
            return result

        # Метод 2: yt-dlp
        result = await self._tiktok_ytdlp(url)
        if result:
            return result
        
        # Метод 2: TikTok API эмуляция
        result = await self._tiktok_api(url)
        if result:
            return result
        
        # Метод 3: Альтернативные сервисы
        result = await self._tiktok_alternative(url)
        if result:
            return result
        
        logger.error(f"Все методы TikTok не сработали для: {url}")
        return None
    
    async def _tiktok_ytdlp(self, url: str) -> Optional[bytes]:
        """Метод 1: yt-dlp для TikTok"""
        try:
            logger.info(f"TikTok yt-dlp: {url}")
            
            ydl_opts = self.ydl_opts.copy()
            ydl_opts.update({
                'format': 'best',
                'extract_flat': False,
                'ignoreerrors': True
            })
            
            def download():
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if info:
                            if info.get('url'):
                                return info.get('url')
                            elif info.get('formats'):
                                for fmt in info.get('formats', []):
                                    if fmt.get('url') and not fmt.get('acodec') == 'none':
                                        return fmt.get('url')
                except Exception as e:
                    logger.debug(f"yt-dlp TikTok error: {e}")
                return None
            
            loop = asyncio.get_event_loop()
            media_url = await loop.run_in_executor(None, download)
            
            if media_url and self.session:
                return await self._download_from_url(media_url)
        
        except Exception as e:
            logger.debug(f"TikTok yt-dlp method failed: {e}")
        return None
    
    async def _tiktok_api(self, url: str) -> Optional[bytes]:
        """Метод 2: TikTok API эмуляция"""
        try:
            logger.info(f"TikTok API: {url}")
            
            # Извлекаем ID видео
            video_id_match = re.search(r'/video/(\d+)', url)
            if not video_id_match:
                return None
            
            video_id = video_id_match.group(1)
            
            # Эмулируем API запрос
            api_url = f"https://api16-normal-useast5a.tiktokv.com/aweme/v1/feed/?aweme_id={video_id}"
            
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    aweme_list = data.get('aweme_list', [])
                    if aweme_list:
                        aweme = aweme_list[0]
                        video = aweme.get('video', {})
                        play_addr = video.get('play_addr', {})
                        url_list = play_addr.get('url_list', [])
                        if url_list:
                            return await self._download_from_url(url_list[0])
        
        except Exception as e:
            logger.debug(f"TikTok API method failed: {e}")
        return None
    
    async def _tiktok_alternative(self, url: str) -> Optional[bytes]:
        """Метод 3: Альтернативные сервисы"""
        try:
            logger.info(f"TikTok alternative: {url}")
            
            # Пробуем разные зеркала и сервисы
            alternatives = [
                f"https://tikmate.online/download?url={url}",
                f"https://musicallydown.com/download?url={url}",
            ]
            
            for alt_url in alternatives:
                try:
                    async with self.session.get(alt_url) as response:
                        if response.status == 200:
                            # Парсим ответ для поиска видео URL
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Ищем прямые ссылки на видео
                            video_links = soup.find_all('a', href=re.compile(r'\.mp4'))
                            if video_links:
                                video_url = video_links[0]['href']
                                return await self._download_from_url(video_url)
                except:
                    continue
        
        except Exception as e:
            logger.debug(f"TikTok alternative method failed: {e}")
        return None
    
    async def download_instagram_media(self, url: str) -> Optional[bytes]:
        """Улучшенное скачивание Instagram"""
        
        # Метод 1: Cobalt API (Самый стабильный)
        result = await self._cobalt_api(url)
        if result:
            return result

        # Метод 2: yt-dlp
        result = await self._instagram_ytdlp(url)
        if result:
            return result
        
        # Метод 2: Внешние сервисы
        result = await self._instagram_instaloader(url)
        if result:
            return result
        
        # Метод 3: Instagram API эмуляция
        result = await self._instagram_api(url)
        if result:
            return result
        
        # Метод 4: Мобильная версия
        result = await self._instagram_mobile(url)
        if result:
            return result
        
        # Метод 5: Простой прямой метод
        result = await self._instagram_simple(url)
        if result:
            return result
        
        # Метод 6: Новый API подход
        result = await self._instagram_new_api(url)
        if result:
            return result
        
        logger.error(f"Все методы Instagram не сработали для: {url}")
        return None
    
    async def _instagram_ytdlp(self, url: str) -> Optional[bytes]:
        """Метод 1: yt-dlp для Instagram"""
        try:
            logger.info(f"Instagram yt-dlp: {url}")
            
            ydl_opts = self.ydl_opts.copy()
            ydl_opts.update({
                'format': 'best',
                'extract_flat': False,
                'ignoreerrors': True
            })
            
            def download():
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if info:
                            if info.get('url'):
                                return info.get('url')
                            elif info.get('formats'):
                                for fmt in info.get('formats', []):
                                    if fmt.get('url'):
                                        return fmt.get('url')
                except Exception as e:
                    logger.debug(f"yt-dlp Instagram error: {e}")
                return None
            
            loop = asyncio.get_event_loop()
            media_url = await loop.run_in_executor(None, download)
            
            if media_url and self.session:
                return await self._download_from_url(media_url)
        
        except Exception as e:
            logger.debug(f"Instagram yt-dlp method failed: {e}")
        return None
    
    async def _instagram_instaloader(self, url: str) -> Optional[bytes]:
        """Метод 2: Внешние сервисы для Instagram"""
        try:
            logger.info(f"Instagram external services: {url}")
            
            # Пробуем разные внешние сервисы
            services = [
                f"https://ddinstagram.com/p/{url.split('/p/')[1].split('/')[0]}",
                f"https://insta-stories-viewer.com/p/{url.split('/p/')[1].split('/')[0]}",
                f"https://dumpinstagram.com/p/{url.split('/p/')[1].split('/')[0]}"
            ]
            
            for service_url in services:
                try:
                    if self.session:
                        async with self.session.get(service_url, timeout=15) as response:
                            if response.status == 200:
                                html = await response.text()
                                
                                # Ищем прямые ссылки
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Ищем видео
                                video_tags = soup.find_all('video')
                                for video in video_tags:
                                    if video.get('src'):
                                        return await self._download_from_url(video.get('src'))
                                
                                # Ищем изображения
                                img_tags = soup.find_all('meta', property='og:image')
                                for img in img_tags:
                                    if img.get('content'):
                                        return await self._download_from_url(img.get('content'))
                                
                                # Ищем в тегах img
                                img_tags = soup.find_all('img')
                                for img in img_tags:
                                    src = img.get('src')
                                    if src and ('cdninstagram.com' in src or 'instagram.com' in src):
                                        return await self._download_from_url(src)
                except:
                    continue
        
        except Exception as e:
            logger.debug(f"Instagram external services method failed: {e}")
        return None
    
    async def _instagram_api(self, url: str) -> Optional[bytes]:
        """Метод 3: Instagram API эмуляция"""
        try:
            logger.info(f"Instagram API: {url}")
            
            # Извлекаем shortcode
            shortcode_match = re.search(r'/p/([^/]+)', url)
            if not shortcode_match:
                return None
            
            shortcode = shortcode_match.group(1)
            
            # Эмулируем API запрос
            api_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
            
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Ищем данные в embedded JSON
                    json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', html)
                    if json_match:
                        data = json.loads(json_match.group(1))
                        
                        # Ищем медиа в данных
                        media_data = data.get('entry_data', {}).get('PostPage', [])
                        if media_data:
                            post = media_data[0].get('graphql', {}).get('shortcode_media', {})
                            
                            if post.get('is_video'):
                                return await self._download_from_url(post.get('video_url'))
                            else:
                                return await self._download_from_url(post.get('display_url'))
        
        except Exception as e:
            logger.debug(f"Instagram API method failed: {e}")
        return None
    
    async def _instagram_simple(self, url: str) -> Optional[bytes]:
        """Метод 5: Простой прямой метод"""
        try:
            logger.info(f"Instagram simple: {url}")
            
            # Извлекаем shortcode
            shortcode = url.split('/p/')[1].split('/')[0]
            
            # Создаем прямую URL для изображения
            direct_url = f"https://instagram.com/p/{shortcode}/media"
            
            if self.session:
                async with self.session.get(direct_url, timeout=15) as response:
                    if response.status == 200:
                        return await response.read()
                    
                    # Пробуем альтернативную URL
                    alt_url = f"https://www.instagram.com/p/{shortcode}/media"
                    async with self.session.get(alt_url, timeout=15) as response:
                        if response.status == 200:
                            return await response.read()
        
        except Exception as e:
            logger.debug(f"Instagram simple method failed: {e}")
        return None
    
    async def _instagram_mobile(self, url: str) -> Optional[bytes]:
        """Метод 4: Мобильная версия Instagram"""
        try:
            logger.info(f"Instagram mobile: {url}")
            
            # Конвертируем URL в мобильную версию
            mobile_url = url.replace('instagram.com', 'ddinstagram.com')
            
            # Пробуем скачать напрямую
            if self.session:
                async with self.session.get(mobile_url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Ищем прямые ссылки на медиа
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Ищем видео
                        video_tags = soup.find_all('video')
                        for video in video_tags:
                            if video.get('src'):
                                return await self._download_from_url(video.get('src'))
                        
                        # Ищем изображения
                        img_tags = soup.find_all('meta', property='og:image')
                        for img in img_tags:
                            if img.get('content'):
                                return await self._download_from_url(img.get('content'))
                        
                        # Ищем в тегах img
                        img_tags = soup.find_all('img')
                        for img in img_tags:
                            src = img.get('src')
                            if src and 'cdninstagram.com' in src:
                                return await self._download_from_url(src)
        
        except Exception as e:
            logger.debug(f"Instagram mobile method failed: {e}")
        return None
    
    async def _instagram_new_api(self, url: str) -> Optional[bytes]:
        """Метод 6: Новый API подход через внешние сервисы"""
        try:
            logger.info(f"Instagram new API: {url}")
            
            async with InstagramAPIDownloader() as api:
                return await api.download_instagram_media(url)
        
        except Exception as e:
            logger.debug(f"Instagram new API method failed: {e}")
        return None
    
    async def _cobalt_api(self, url: str) -> List[dict]:
        """Универсальный метод через Cobalt API. Возвращает список media-словарей."""
        try:
            logger.info(f"Cobalt API: {url}")
            
            instances = [
                "https://api.cobalt.tools",
                "https://co.wuk.sh",
                "https://api.wuk.sh",
                "https://cobalt.kanzen.me",
            ]
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            payload = {
                "url": url,
                "videoQuality": "max",
                "filenamePattern": "basic",
                "isAudioOnly": False,
                "disableMetadata": False # Нам нужны метаданные для текста
            }
            
            for base_url in instances:
                try:
                    result_items = []
                    api_url = f"{base_url}/api/json"
                    async with self.session.post(api_url, json=payload, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('status') == 'error':
                                logger.debug(f"Cobalt error on {base_url}: {data.get('text')}")
                                continue
                                
                            # Если это стрим/пикер (карусель)
                            if data.get('picker'):
                                for item in data['picker']:
                                    if item.get('url'):
                                        content = await self._download_from_url(item['url'])
                                        if content:
                                            result_items.append({'data': content, 'url': item['url']})
                            
                            # Одиночное медиа
                            elif data.get('url'):
                                content = await self._download_from_url(data['url'])
                                if content:
                                    result_items.append({'data': content, 'url': data['url']})
                            
                            if result_items:
                                logger.info(f"Got {len(result_items)} items from Cobalt ({base_url})")
                                return result_items
                                
                except Exception as e:
                    logger.debug(f"Failed Cobalt instance {base_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Cobalt API method failed: {e}")
        return []

    async def _download_from_url(self, url: str) -> Optional[bytes]:
        """Скачивает медиа из URL"""
        try:
            if not self.session or not url:
                return None
            
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    content = await response.read()
                    if len(content) > 1024:  # Проверяем что файл не пустой
                        return content
                    else:
                        logger.warning(f"Media file is too small: {len(content)} bytes")
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading from {url}")
        except Exception as e:
            logger.error(f"Error downloading from {url}: {e}")
        
        return None
    
    async def download_media(self, url: str) -> dict:
        """Основной метод скачивания медиа. Возвращает словарь с items и text."""
        platform = self.detect_platform(url)
        results = []
        post_text = None
        
        # Сначала пробуем Cobalt (он лучший для каруселей и видео)
        cobalt_items = await self._cobalt_api(url)
        if cobalt_items:
            for item in cobalt_items:
                data, ftype = self._identify_media_type(item['data'])
                results.append({'data': data, 'type': ftype})
        
        # Если Cobalt не сработал или пустой, пробуем специфические методы (одиночные)
        if not results:
            data = None
            if platform == 'pinterest':
                data = await self.download_pinterest_media(url)
            elif platform == 'tiktok':
                data = await self.download_tiktok_media(url)
            elif platform == 'instagram':
                data = await self.download_instagram_media(url)
            
            if data:
                data, ftype = self._identify_media_type(data)
                results.append({'data': data, 'type': ftype})

        # Попытка извлечь текст (упрощенный скрапинг)
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    meta_desc = soup.find('meta', property='og:description')
                    if meta_desc:
                        post_text = meta_desc.get('content')
        except:
            pass
            
        return {'items': results, 'text': post_text}

    def _identify_media_type(self, data: bytes) -> tuple[bytes, str]:
        """Определяет тип файла по заголовку"""
        if len(data) > 8 and data[4:8] == b'ftyp':
            return data, 'video'
        elif data.startswith(b'\xff\xd8\xff'):
            return data, 'photo'
        elif data.startswith(b'\x89PNG'):
            return data, 'photo'
        elif data.startswith(b'\x1a\x45\xdf\xa3'):
            return data, 'video'
        elif data.startswith(b'GIF8'):
            return data, 'video'
            
        file_type = 'video' if len(data) > 2 * 1024 * 1024 else 'photo'
        return data, file_type

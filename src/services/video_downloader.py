import aiohttp
import asyncio
import re
import json
from typing import Optional, Dict, Any
from loguru import logger
from bs4 import BeautifulSoup

class VideoDownloader:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=45),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def download_instagram_video(self, url: str) -> Optional[bytes]:
        """Скачать видео из Instagram через множественные методы"""
        
        # Извлекаем shortcode
        shortcode_match = re.search(r'/p/([^/]+)', url)
        if not shortcode_match:
            return None
        
        shortcode = shortcode_match.group(1)
        logger.info(f"Downloading Instagram video: {shortcode}")
        
        # Метод 1: Instagram Direct API
        video_data = await self._instagram_direct_api(shortcode)
        if video_data:
            return video_data
        
        # Метод 2: Instagram JSON scraping
        video_data = await self._instagram_json_scraping(shortcode)
        if video_data:
            return video_data
        
        # Метод 3: Instagram GraphQL
        video_data = await self._instagram_graphql(shortcode)
        if video_data:
            return video_data
        
        # Метод 4: Instagram Mobile
        video_data = await self._instagram_mobile(shortcode)
        if video_data:
            return video_data
        
        # Метод 5: Внешние видео сервисы
        video_data = await self._instagram_video_services(url)
        if video_data:
            return video_data
        
        logger.error(f"All Instagram video methods failed for {shortcode}")
        return None
    
    async def _instagram_direct_api(self, shortcode: str) -> Optional[bytes]:
        """Метод 1: Instagram Direct API"""
        try:
            api_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
            
            async with self.session.get(api_url, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Ищем видео URL в embed
                    video_match = re.search(r'"video_url":"([^"]+)"', html)
                    if video_match:
                        video_url = video_match.group(1).replace('\\/', '/')
                        return await self._download_video_from_url(video_url)
                    
                    # Ищем в JSON данных
                    json_match = re.search(r'window\._sharedData = ({.+?});', html)
                    if json_match:
                        data = json.loads(json_match.group(1))
                        video_url = self._extract_video_from_shared_data(data)
                        if video_url:
                            return await self._download_video_from_url(video_url)
        
        except Exception as e:
            logger.debug(f"Instagram direct API failed: {e}")
        return None
    
    async def _instagram_json_scraping(self, shortcode: str) -> Optional[bytes]:
        """Метод 2: Instagram JSON scraping"""
        try:
            url = f"https://www.instagram.com/p/{shortcode}/"
            
            async with self.session.get(url, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Ищем дополнительные данные
                    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
                    
                    for script in scripts:
                        if 'graphql' in script or 'media' in script:
                            # Ищем JSON данные в скриптах
                            json_matches = re.findall(r'({[^{}]*(?:{[^{}]*}[^{}]*)*})', script)
                            for json_str in json_matches:
                                try:
                                    data = json.loads(json_str)
                                    video_url = self._extract_video_from_data(data)
                                    if video_url:
                                        return await self._download_video_from_url(video_url)
                                except:
                                    continue
        
        except Exception as e:
            logger.debug(f"Instagram JSON scraping failed: {e}")
        return None
    
    async def _instagram_graphql(self, shortcode: str) -> Optional[bytes]:
        """Метод 3: Instagram GraphQL"""
        try:
            # GraphQL запрос для получения медиа
            query_hash = "9b498c08113f1e09617a1703c22b2f32"
            variables = {
                "shortcode": shortcode,
                "child_comment_count": 3,
                "fetch_comment_count": 40,
                "parent_comment_count": 24,
                "has_threaded_comments": True
            }
            
            api_url = "https://www.instagram.com/graphql/query/"
            params = {
                "query_hash": query_hash,
                "variables": json.dumps(variables)
            }
            
            async with self.session.get(api_url, params=params, timeout=20) as response:
                if response.status == 200:
                    data = await response.json()
                    video_url = self._extract_video_from_graphql(data)
                    if video_url:
                        return await self._download_video_from_url(video_url)
        
        except Exception as e:
            logger.debug(f"Instagram GraphQL failed: {e}")
        return None
    
    async def _instagram_mobile(self, shortcode: str) -> Optional[bytes]:
        """Метод 4: Instagram Mobile"""
        try:
            mobile_urls = [
                f"https://ddinstagram.com/p/{shortcode}/",
                f"https://instagram.com/p/{shortcode}/embed/",
                f"https://instagr.am/p/{shortcode}/"
            ]
            
            for mobile_url in mobile_urls:
                async with self.session.get(mobile_url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Ищем видео теги
                        soup = BeautifulSoup(html, 'html.parser')
                        video_tags = soup.find_all('video')
                        
                        for video in video_tags:
                            src = video.get('src')
                            if src and ('mp4' in src or 'm3u8' in src):
                                return await self._download_video_from_url(src)
                        
                        # Ищем в meta тегах
                        meta_video = soup.find('meta', property='og:video')
                        if meta_video and meta_video.get('content'):
                            return await self._download_video_from_url(meta_video.get('content'))
        
        except Exception as e:
            logger.debug(f"Instagram mobile failed: {e}")
        return None
    
    async def _instagram_video_services(self, original_url: str) -> Optional[bytes]:
        """Метод 5: Внешние видео сервисы"""
        try:
            services = [
                {
                    'name': 'InstaSave',
                    'url': f'https://instasave.website/download?url={original_url}',
                    'parser': self._parse_instasave_video
                },
                {
                    'name': 'DownloadGram',
                    'url': f'https://downloadgram.org/download?url={original_url}',
                    'parser': self._parse_downloadgram_video
                },
                {
                    'name': 'InstaDownloader',
                    'url': f'https://instadownloader.co/api?url={original_url}',
                    'parser': self._parse_instadownloader_video
                }
            ]
            
            for service in services:
                try:
                    async with self.session.get(service['url'], timeout=15) as response:
                        if response.status == 200:
                            content = await response.text()
                            video_url = await service['parser'](content)
                            if video_url:
                                return await self._download_video_from_url(video_url)
                except:
                    continue
        
        except Exception as e:
            logger.debug(f"Instagram video services failed: {e}")
        return None
    
    async def download_tiktok_video(self, url: str) -> Optional[bytes]:
        """Скачать видео из TikTok"""
        try:
            logger.info(f"Downloading TikTok video: {url}")
            
            # Метод 1: TikTok Direct API
            video_data = await self._tiktok_direct_api(url)
            if video_data:
                return video_data
            
            # Метод 2: TikTok Mobile
            video_data = await self._tiktok_mobile(url)
            if video_data:
                return video_data
            
            # Метод 3: TikTok Services
            video_data = await self._tiktok_services(url)
            if video_data:
                return video_data
        
        except Exception as e:
            logger.debug(f"TikTok video download failed: {e}")
        return None
    
    async def _tiktok_direct_api(self, url: str) -> Optional[bytes]:
        """TikTok Direct API"""
        try:
            # Извлекаем видео ID
            video_id_match = re.search(r'/video/(\d+)', url)
            if not video_id_match:
                return None
            
            video_id = video_id_match.group(1)
            
            # TikTok API endpoint
            api_url = f"https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={video_id}"
            
            async with self.session.get(api_url, timeout=20) as response:
                if response.status == 200:
                    data = await response.json()
                    video_url = self._extract_tiktok_video(data)
                    if video_url:
                        return await self._download_video_from_url(video_url)
        
        except Exception as e:
            logger.debug(f"TikTok direct API failed: {e}")
        return None
    
    async def _tiktok_mobile(self, url: str) -> Optional[bytes]:
        """TikTok Mobile"""
        try:
            mobile_url = url.replace('tiktok.com', 'vm.tiktok.com')
            
            async with self.session.get(mobile_url, timeout=15) as response:
                if response.status == 200:
                    # Следуем за редиректом
                    final_url = str(response.url)
                    
                    # Ищем видео в странице
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    video_tags = soup.find_all('video')
                    for video in video_tags:
                        src = video.get('src')
                        if src and 'mp4' in src:
                            return await self._download_video_from_url(src)
        
        except Exception as e:
            logger.debug(f"TikTok mobile failed: {e}")
        return None
    
    async def _tiktok_services(self, url: str) -> Optional[bytes]:
        """TikTok Services"""
        try:
            services = [
                f'https://tikmate.online/download?url={url}',
                f'https://snaptik.app/abc?url={url}',
                f'https://musicaldown.com/download?url={url}'
            ]
            
            for service_url in services:
                try:
                    async with self.session.get(service_url, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Ищем видео URL
                            video_match = re.search(r'(https://[^"\s]+\.mp4[^"\s]*)', html)
                            if video_match:
                                return await self._download_video_from_url(video_match.group(1))
                except:
                    continue
        
        except Exception as e:
            logger.debug(f"TikTok services failed: {e}")
        return None
    
    async def _download_video_from_url(self, video_url: str) -> Optional[bytes]:
        """Скачать видео из URL"""
        try:
            if not self.session or not video_url:
                return None
            
            headers = {
                'Referer': 'https://www.instagram.com/',
                'Origin': 'https://www.instagram.com'
            }
            
            async with self.session.get(video_url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    video_data = await response.read()
                    if len(video_data) > 1024:  # Проверяем что файл не пустой
                        return video_data
        
        except Exception as e:
            logger.debug(f"Video download from URL failed: {e}")
        return None
    
    def _extract_video_from_shared_data(self, data: Dict) -> Optional[str]:
        """Извлечь видео URL из shared data"""
        try:
            entry_data = data.get('entry_data', {})
            post_page = entry_data.get('PostPage', [{}])[0]
            graphql = post_page.get('graphql', {})
            shortcode_media = graphql.get('shortcode_media', {})
            
            if shortcode_media.get('is_video'):
                return shortcode_media.get('video_url')
            
            # Проверяем edge_sidecar_to_children (карусели)
            edge_sidecar = shortcode_media.get('edge_sidecar_to_children', {})
            edges = edge_sidecar.get('edges', [])
            
            for edge in edges:
                node = edge.get('node', {})
                if node.get('is_video'):
                    return node.get('video_url')
        
        except Exception as e:
            logger.debug(f"Extract video from shared data failed: {e}")
        return None
    
    def _extract_video_from_data(self, data: Any) -> Optional[str]:
        """Извлечь видео URL из данных"""
        try:
            if isinstance(data, dict):
                # Рекурсивный поиск видео URL
                for key, value in data.items():
                    if key == 'video_url' and isinstance(value, str):
                        return value
                    if isinstance(value, (dict, list)):
                        result = self._extract_video_from_data(value)
                        if result:
                            return result
            elif isinstance(data, list):
                for item in data:
                    result = self._extract_video_from_data(item)
                    if result:
                        return result
        
        except Exception as e:
            logger.debug(f"Extract video from data failed: {e}")
        return None
    
    def _extract_video_from_graphql(self, data: Dict) -> Optional[str]:
        """Извлечь видео URL из GraphQL"""
        try:
            media = data.get('data', {}).get('shortcode_media', {})
            
            if media.get('is_video'):
                return media.get('video_url')
            
            # Проверяем carousel_media
            carousel_media = media.get('carousel_media', [])
            for media_item in carousel_media:
                if media_item.get('is_video'):
                    return media_item.get('video_url')
        
        except Exception as e:
            logger.debug(f"Extract video from GraphQL failed: {e}")
        return None
    
    def _extract_tiktok_video(self, data: Dict) -> Optional[str]:
        """Извлечь видео URL из TikTok данных"""
        try:
            aweme_list = data.get('aweme_list', [])
            if aweme_list:
                aweme = aweme_list[0]
                video = aweme.get('video', {})
                play_addr = video.get('play_addr', {})
                url_list = play_addr.get('url_list', [])
                
                if url_list:
                    return url_list[0]  # Берем первый URL (лучшее качество)
        
        except Exception as e:
            logger.debug(f"Extract TikTok video failed: {e}")
        return None
    
    async def _parse_instasave_video(self, content: str) -> Optional[str]:
        """Парсер для InstaSave видео"""
        try:
            # Ищем видео URL в ответе
            video_match = re.search(r'"video_url":"([^"]+)"', content)
            if video_match:
                return video_match.group(1).replace('\\/', '/')
            
            # Ищем в JSON
            data = json.loads(content)
            if data.get('video_url'):
                return data['video_url']
        except:
            pass
        return None
    
    async def _parse_downloadgram_video(self, content: str) -> Optional[str]:
        """Парсер для DownloadGram видео"""
        try:
            data = json.loads(content)
            if data.get('success') and data.get('data'):
                media_data = data['data'][0] if data['data'] else {}
                return media_data.get('url') or media_data.get('download_url')
        except:
            pass
        return None
    
    async def _parse_instadownloader_video(self, content: str) -> Optional[str]:
        """Парсер для InstaDownloader видео"""
        try:
            # Ищем прямые ссылки на видео
            url_match = re.search(r'(https://[^"\s]+\.mp4[^"\s]*)', content, re.IGNORECASE)
            if url_match:
                return url_match.group(1)
        except:
            pass
        return None

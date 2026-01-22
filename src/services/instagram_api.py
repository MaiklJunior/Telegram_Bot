import aiohttp
import asyncio
import re
from typing import Optional
from loguru import logger

class InstagramAPIDownloader:
    def __init__(self):
        self.session = None
    
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
    
    async def download_instagram_media(self, url: str) -> Optional[bytes]:
        """Скачать медиа через внешние API сервисы"""
        
        # Извлекаем shortcode
        shortcode_match = re.search(r'/p/([^/]+)', url)
        if not shortcode_match:
            return None
        
        shortcode = shortcode_match.group(1)
        
        # Пробуем разные API сервисы
        apis = [
            {
                'name': 'InstaSave',
                'url': f'https://instasave.website/download?url={url}',
                'parser': self._parse_instasave
            },
            {
                'name': 'DownloadGram',
                'url': f'https://downloadgram.org/download?url={url}',
                'parser': self._parse_downloadgram
            },
            {
                'name': 'InstaDownloader',
                'url': f'https://instadownloader.co/api?url={url}',
                'parser': self._parse_instadownloader
            },
            {
                'name': 'SaveInsta',
                'url': f'https://saveinsta.app/api?url={url}',
                'parser': self._parse_saveinsta
            },
            {
                'name': 'InstaMoe',
                'url': f'https://insta-moe.com/api?url={url}',
                'parser': self._parse_instamoe
            }
        ]
        
        for api in apis:
            try:
                logger.info(f"Trying {api['name']} API for {shortcode}")
                
                async with self.session.get(api['url'], timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Парсим ответ
                        media_url = await api['parser'](content, url)
                        if media_url:
                            # Скачиваем медиа
                            async with self.session.get(media_url, timeout=20) as media_response:
                                if media_response.status == 200:
                                    media_data = await media_response.read()
                                    if len(media_data) > 1024:  # Проверяем что файл не пустой
                                        logger.info(f"Successfully downloaded via {api['name']}")
                                        return media_data
                    else:
                        logger.warning(f"{api['name']} returned status {response.status}")
                        
            except Exception as e:
                logger.debug(f"{api['name']} failed: {e}")
                continue
        
        logger.error(f"All API services failed for {shortcode}")
        return None
    
    async def _parse_instasave(self, content: str, original_url: str) -> Optional[str]:
        """Парсер для InstaSave"""
        import json
        try:
            # Ищем URL в ответе
            url_match = re.search(r'"download_url":"([^"]+)"', content)
            if url_match:
                return url_match.group(1).replace('\\/', '/')
            
            # Пробуем JSON
            data = json.loads(content)
            if data.get('download_url'):
                return data['download_url']
        except:
            pass
        return None
    
    async def _parse_downloadgram(self, content: str, original_url: str) -> Optional[str]:
        """Парсер для DownloadGram"""
        import json
        try:
            data = json.loads(content)
            if data.get('success') and data.get('data'):
                media_data = data['data'][0] if data['data'] else {}
                return media_data.get('url') or media_data.get('download_url')
        except:
            pass
        return None
    
    async def _parse_instadownloader(self, content: str, original_url: str) -> Optional[str]:
        """Парсер для InstaDownloader"""
        try:
            # Ищем прямые ссылки на медиа
            url_match = re.search(r'(https://[^"\s]+\.(jpg|jpeg|png|mp4)[^"\s]*)', content, re.IGNORECASE)
            if url_match:
                return url_match.group(1)
        except:
            pass
        return None
    
    async def _parse_saveinsta(self, content: str, original_url: str) -> Optional[str]:
        """Парсер для SaveInsta"""
        import json
        try:
            data = json.loads(content)
            if data.get('status') == 'ok' and data.get('data'):
                media_item = data['data'][0] if data['data'] else {}
                return media_item.get('url') or media_item.get('download_url')
        except:
            pass
        return None
    
    async def _parse_instamoe(self, content: str, original_url: str) -> Optional[str]:
        """Парсер для InstaMoe"""
        try:
            # Ищем URL в HTML ответе
            url_match = re.search(r'href="(https://[^"]+\.(jpg|jpeg|png|mp4)[^"]*)"', content, re.IGNORECASE)
            if url_match:
                return url_match.group(1)
        except:
            pass
        return None

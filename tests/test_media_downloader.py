import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.services.media_downloader import MediaDownloader


class TestMediaDownloader:
    """Тесты для сервиса скачивания медиа"""
    
    @pytest.fixture
    async def downloader(self):
        """Фикстура для создания экземпляра MediaDownloader"""
        async with MediaDownloader() as downloader:
            yield downloader
    
    def test_detect_platform_pinterest(self):
        """Тест определения Pinterest"""
        downloader = MediaDownloader()
        
        assert downloader.detect_platform("https://pinterest.com/pin/123456/") == "pinterest"
        assert downloader.detect_platform("https://pin.it/123456") == "pinterest"
        assert downloader.detect_platform("https://www.pinterest.com/pin/123456/") == "pinterest"
    
    def test_detect_platform_tiktok(self):
        """Тест определения TikTok"""
        downloader = MediaDownloader()
        
        assert downloader.detect_platform("https://tiktok.com/@user/video/123456") == "tiktok"
        assert downloader.detect_platform("https://www.tiktok.com/@user/video/123456") == "tiktok"
    
    def test_detect_platform_instagram(self):
        """Тест определения Instagram"""
        downloader = MediaDownloader()
        
        assert downloader.detect_platform("https://instagram.com/p/123456/") == "instagram"
        assert downloader.detect_platform("https://www.instagram.com/p/123456/") == "instagram"
        assert downloader.detect_platform("https://instagr.am/p/123456/") == "instagram"
    
    def test_detect_platform_unknown(self):
        """Тест определения неизвестной платформы"""
        downloader = MediaDownloader()
        
        assert downloader.detect_platform("https://youtube.com/watch?v=123456") == "unknown"
        assert downloader.detect_platform("https://example.com/video") == "unknown"
    
    @pytest.mark.asyncio
    async def test_download_media_invalid_url(self, downloader):
        """Тест скачивания медиа с невалидным URL"""
        media_data, file_type = await downloader.download_media("https://example.com")
        
        assert media_data is None
        assert file_type == "unknown"
    
    @pytest.mark.asyncio
    @patch('src.services.media_downloader.yt_dlp.YoutubeDL')
    async def test_download_tiktok_success(self, mock_ydl, downloader):
        """Тест успешного скачивания с TikTok"""
        # Мокаем yt-dlp
        mock_instance = AsyncMock()
        mock_instance.extract_info.return_value = {"url": "https://example.com/video.mp4"}
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        # Мокаем HTTP запрос
        with patch.object(downloader.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read.return_value = b"fake_video_data"
            mock_get.return_value.__aenter__.return_value = mock_response
            
            media_data = await downloader.download_tiktok_media("https://tiktok.com/@user/video/123456")
            
            assert media_data == b"fake_video_data"
    
    @pytest.mark.asyncio
    @patch('src.services.media_downloader.yt_dlp.YoutubeDL')
    async def test_download_pinterest_success(self, mock_ydl, downloader):
        """Тест успешного скачивания с Pinterest"""
        # Мокаем yt-dlp
        mock_instance = AsyncMock()
        mock_instance.extract_info.return_value = {"url": "https://example.com/image.jpg"}
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        # Мокаем HTTP запрос
        with patch.object(downloader.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read.return_value = b"fake_image_data"
            mock_get.return_value.__aenter__.return_value = mock_response
            
            media_data = await downloader.download_pinterest_media("https://pinterest.com/pin/123456")
            
            assert media_data == b"fake_image_data"


if __name__ == "__main__":
    pytest.main([__file__])

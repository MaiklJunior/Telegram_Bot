import os
import sys
from fastapi import FastAPI, Request
import uvicorn
import json

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from bot.modern_bot import modern_bot
except ImportError as e:
    print(f"Import error: {e}")
    # Пробуем альтернативный импорт
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'bot'))
    from modern_bot import modern_bot

app = FastAPI(
    title="Modern Telegram Media Downloader",
    description="Advanced media downloader bot for Pinterest, TikTok, Instagram",
    version="2.0"
)

@app.on_event("startup")
async def startup_event():
    """Инициализация бота при запуске"""
    await modern_bot.init_bot()
    print("🚀 Modern Telegram Bot initialized for webhook mode")

@app.get("/")
async def root():
    return {
        "status": "Modern Telegram Media Downloader is running",
        "version": "2.0",
        "platforms": ["Pinterest", "TikTok", "Instagram"],
        "features": ["100% download attempts", "Multiple methods", "Best quality"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "bot": "ready"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        
        # Проверяем что это обновление от Telegram
        if not isinstance(data, dict) or 'update_id' not in data:
            return {"error": "Not a Telegram update"}
        
        # Обрабатываем обновление
        await modern_bot.handle_webhook_update(data)
        
        return {"status": "ok", "bot": "modern"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"error": str(e)}

@app.get("/info")
async def info():
    """Информация о боте"""
    return {
        "name": "Modern Media Downloader Bot",
        "description": "Advanced Telegram bot for downloading media from social platforms",
        "platforms": {
            "Pinterest": "Images, pins, videos",
            "TikTok": "Videos without watermark",
            "Instagram": "Photos, videos, Reels"
        },
        "features": [
            "Multiple download methods per platform",
            "100% success rate attempts",
            "Best available quality",
            "Modern UI with inline keyboards",
            "Error handling and retry options"
        ],
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health", 
            "info": "/info",
            "root": "/"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

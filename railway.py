import os
import sys
from fastapi import FastAPI, Request
import uvicorn
import json
import asyncio

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bot.simple_bot import simple_bot

app = FastAPI()

# Глобальная переменная для бота
bot = None

async def get_bot():
    global bot
    if bot is None:
        bot = simple_bot
        await bot.__aenter__()
    return bot

@app.on_event("startup")
async def startup_event():
    """Инициализация бота при запуске"""
    global bot
    bot = simple_bot
    await bot.__aenter__()
    print("🚀 Simple Telegram bot initialized for webhook mode")

@app.get("/")
async def root():
    return {
        "status": "Simple Media Downloader is running",
        "version": "1.0",
        "platforms": ["Pinterest", "TikTok"],
        "features": ["Direct download", "Best quality", "Simple interface"]
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
        
        # Получаем инициализированный бот
        bot = await get_bot()
        
        # Создаем временное сообщение для обработки
        from aiogram.types import Update
        update = Update.model_validate(data)
        
        # Обрабатываем обновление
        await bot.dp.feed_update(bot.bot, update)
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

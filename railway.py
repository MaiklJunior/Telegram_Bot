import os
import sys
from fastapi import FastAPI, Request
import uvicorn
import json

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bot.main import bot_instance

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Telegram bot is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        
        # Проверяем что это обновление от Telegram
        if not isinstance(data, dict) or 'update_id' not in data:
            return {"error": "Not a Telegram update"}
        
        # Обрабатываем обновление
        await bot_instance.handle_webhook_update(data)
        
        return {"status": "ok"}
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

import json
import asyncio
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot.main import bot_instance


async def handler(request):
    """Handler для Vercel"""
    
    # Получаем тело запроса
    if request.method == 'POST':
        try:
            body = await request.json()
        except:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid JSON'})
            }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'Telegram bot is running'})
        }
    
    # Проверяем что это обновление от Telegram
    if not isinstance(body, dict) or 'update_id' not in body:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Not a Telegram update'})
        }
    
    try:
        # Обрабатываем обновление
        await bot_instance.handle_webhook_update(body)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


# Vercel entry point
async def main(request):
    return await handler(request)

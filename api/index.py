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
def lambda_handler(event, context):
    """AWS Lambda style handler для Vercel"""
    import asyncio
    
    # Конвертируем event в request объект
    class MockRequest:
        def __init__(self, event):
            self.method = event.get('httpMethod', 'GET')
            self.headers = event.get('headers', {})
            
            # Парсим тело
            body = event.get('body', '{}')
            if isinstance(body, str):
                self._body = body
            else:
                self._body = json.dumps(body) if body else '{}'
        
        async def json(self):
            return json.loads(self._body)
    
    request = MockRequest(event)
    
    # Запускаем асинхронный handler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(handler(request))
        return {
            'statusCode': result['statusCode'],
            'body': result['body'],
            'headers': {'Content-Type': 'application/json'}
        }
    finally:
        loop.close()


# Для Vercel
async def main(request):
    return await handler(request)

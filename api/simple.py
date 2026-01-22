import json

def handler(event, context):
    """Simple handler for Vercel"""
    
    try:
        # Для GET запросов
        if event.get('httpMethod') == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'Telegram bot is running'})
            }
        
        # Для POST запросов (webhook)
        if event.get('httpMethod') == 'POST':
            body = event.get('body', '{}')
            if isinstance(body, str):
                data = json.loads(body)
            else:
                data = body
            
            # Проверяем что это обновление от Telegram
            if not isinstance(data, dict) or 'update_id' not in data:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Not a Telegram update'})
                }
            
            # Здесь будет обработка webhook
            # Пока просто возвращаем успех
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok'})
            }
        
        # Другие методы
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

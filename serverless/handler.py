import json
import asyncio
from typing import Dict, Any
from loguru import logger

# Добавляем путь к src в Python path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot.main import bot_instance


async def async_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """Асинхронный обработчик для serverless платформы"""
    
    # Определяем тип платформы по структуре события
    if 'body' in event:
        # AWS Lambda / Yandex Cloud Functions
        try:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
    else:
        # Другие форматы
        body = event
    
    # Проверяем, что это обновление от Telegram
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
        logger.error(f"Ошибка при обработке обновления: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """Основной handler для serverless платформы"""
    
    # Настройка логирования для serverless
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="{time:HH:mm:ss} | {level} | {message}"
    )
    
    # Запускаем асинхронный обработчик
    return asyncio.run(async_handler(event))


# Для Yandex Cloud Functions
def yandex_handler(event, context):
    """Handler для Yandex Cloud Functions"""
    return handler(event, context)


# Для AWS Lambda
def lambda_handler(event, context):
    """Handler для AWS Lambda"""
    return handler(event, context)


# Для других платформ
def main_handler(event, context=None):
    """Универсальный handler"""
    return handler(event, context)

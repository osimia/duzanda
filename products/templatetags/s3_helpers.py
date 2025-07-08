import requests
import logging
from django.conf import settings
from django.core.cache import cache
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def check_s3_file_exists(url, timeout=3, cache_timeout=3600):
    """
    Проверяет существование файла в Selectel S3 по URL.
    Результаты кэшируются для оптимизации.
    
    Args:
        url (str): URL-адрес файла для проверки
        timeout (int): Таймаут для запроса (в секундах)
        cache_timeout (int): Время хранения результата в кэше (в секундах)
        
    Returns:
        bool: True если файл существует, иначе False
    """
    if not url:
        return False
        
    # Проверяем кэш
    cache_key = f"s3_file_exists:{url}"
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result
        
    try:
        # Выполняем HEAD-запрос чтобы не скачивать весь файл
        response = requests.head(url, timeout=timeout)
        exists = response.status_code == 200
        
        # Кэшируем результат
        cache.set(cache_key, exists, cache_timeout)
        
        return exists
    except Exception as e:
        logger.error(f"Error checking S3 file: {url}, error: {str(e)}")
        return False

def get_fallback_image_url():
    """
    Возвращает URL для запасного изображения.
    """
    return '/static/images/no-image.png'

from django import template
from urllib.parse import urlparse, quote
import logging
from .s3_helpers import check_s3_file_exists, get_fallback_image_url

register = template.Library()
logger = logging.getLogger(__name__)

@register.filter
def s3_image_url(image_field):
    """
    Фильтр шаблона для корректного формирования URL к изображениям в Selectel S3.
    Пример использования: {{ product.image|s3_image_url }}
    """
    if not image_field:
        return ''
    
    try:
        # Проверяем, есть ли модель ProductImage и метод get_direct_s3_url
        if hasattr(image_field, 'get_direct_s3_url'):
            direct_url = image_field.get_direct_s3_url()
            if direct_url:
                return direct_url
        
        # Пытаемся получить URL непосредственно из поля
        url = image_field.url
        
        # Проверяем, содержит ли URL схему
        if not url.startswith(('http://', 'https://')):
            # Если нет схемы, добавляем https://
            url = f"https://{url}"
        
        # Разбираем URL для анализа
        parsed_url = urlparse(url)
        
        # Проверяем, есть ли в пути двойные слеши
        path = parsed_url.path
        while '//' in path:
            path = path.replace('//', '/')
        
        # Кодируем специальные символы в пути
        path_parts = path.split('/')
        encoded_parts = [quote(part) for part in path_parts if part]  # Убираем пустые строки
        encoded_path = '/' + '/'.join(encoded_parts) if encoded_parts else '/'
        
        # Собираем URL обратно
        fixed_url = f"{parsed_url.scheme}://{parsed_url.netloc}{encoded_path}"
        
        # Логируем URL для отладки
        logger.debug(f"Original URL: {url}, Fixed URL: {fixed_url}")
        
        return fixed_url
    except Exception as e:
        # В случае любой ошибки записываем в лог и возвращаем пустую строку
        logger.error(f"Error generating S3 URL: {str(e)}")
        # Если это для разработки, можно вернуть заглушку
        from django.conf import settings
        if settings.DEBUG:
            return '/static/images/no-image.png'
        return ''

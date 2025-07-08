from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
import os
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class MediaStorage(S3Boto3Storage):
    location = 'media'  # Папка в S3, куда будут загружаться файлы
    file_overwrite = False  # Запретить перезапись файлов с одинаковыми именами
    
class ProductImagesStorage(S3Boto3Storage):
    """
    Хранилище для изображений продуктов в S3
    """
    location = 'product_images'  # Отдельная папка для изображений продуктов
    file_overwrite = False  # Запретить перезапись файлов
    
    # Настройки для публичного доступа к файлам
    querystring_auth = False  # Отключаем авторизационные query-параметры для прямых ссылок
    default_acl = 'public-read'  # Файлы будут публичными
    # НЕ используем custom_domain, так как он вызывает проблемы с URL
    # Вместо этого будем работать с полными URL от Selectel
    
    # Настройки для стабильной работы с Selectel S3
    connect_timeout = 60  # Увеличиваем таймаут подключения до 60 секунд
    read_timeout = 60  # Увеличиваем таймаут чтения до 60 секунд
    
    def _save(self, name, content):
        """
        Переопределяем метод _save для прямой загрузки в S3 без промежуточного сохранения
        """
        # Используем более простую схему имен файлов
        import datetime
        import uuid
        import os
        
        # Получаем расширение файла
        _, ext = os.path.splitext(name)
        
        # Генерируем уникальное короткое имя с UUID4 (без дефисов)
        unique_id = uuid.uuid4().hex[:8]  # Берем только первые 8 символов для краткости
        timestamp = datetime.datetime.now().strftime('%Y%m%d')
        
        # Формируем новое имя файла: timestamp_uuid_ext
        name = f"{timestamp}_{unique_id}{ext}"
        
        return super()._save(name, content)
        
    def url(self, name, parameters=None, expire=None):
        """
        Переопределяем метод url для корректного формирования URL к файлам в Selectel S3
        """
        from django.conf import settings
        from urllib.parse import quote
        
        logger.debug(f"Generating URL for file: {name}")
        
        if not name:
            logger.warning("Empty name provided to url method")
            return ""
        
        # Проверяем, есть ли настройка для прямого URL Selectel
        direct_storage_url = getattr(settings, 'SELECTEL_DIRECT_STORAGE_URL', None)
        
        if direct_storage_url:
            try:
                # Обрабатываем имя файла
                if name.startswith('/'):
                    name = name[1:]
                    
                # Если есть location в имени файла, удаляем его
                location = self.location.strip('/')
                if name.startswith(f"{location}/"):
                    name = name[len(f"{location}/"):]
                
                # Кодируем имя файла для URL
                encoded_name = quote(name)
                
                # Формируем URL в формате Selectel Storage
                url = f"{direct_storage_url}/{self.location}/{encoded_name}"
                logger.debug(f"Generated direct S3 URL: {url}")
                return url
            except Exception as e:
                logger.error(f"Error generating direct URL: {str(e)}")
                # Если произошла ошибка, пробуем запасной вариант
        
        # Запасной вариант - старый метод
        try:
            # Формируем URL вручную для большей надежности
            endpoint = settings.AWS_S3_ENDPOINT_URL.rstrip('/')
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            location = self.location.strip('/')
            
            # Обрабатываем имя файла
            if name.startswith('/'):
                name = name[1:]
            
            # Кодируем имя файла
            encoded_name = quote(name)
            
            # Собираем полный URL
            full_url = f"{endpoint}/{bucket}/{location}/{encoded_name}"
            
            # Удаляем двойные слеши в пути (кроме протокола)
            parts = full_url.split('://')
            if len(parts) > 1:
                protocol = parts[0]
                path = parts[1]
                while '//' in path:
                    path = path.replace('//', '/')
                full_url = f"{protocol}://{path}"
                
            logger.debug(f"Generated alternative URL: {full_url}")
            return full_url
        except Exception as e:
            logger.error(f"Error generating alternative URL: {str(e)}")
            # Если что-то пошло не так, возвращаем оригинальный метод
            try:
                url = super().url(name, parameters=parameters, expire=expire)
                logger.debug(f"Using original method URL: {url}")
                return url
            except Exception as e2:
                logger.error(f"Error in original url method: {str(e2)}")
                return ""
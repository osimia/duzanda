"""
Тестовое представление для проверки доступности файлов в Selectel S3
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from .models import ProductImage
from .templatetags.s3_helpers import check_s3_file_exists

@staff_member_required
def check_s3_images(request):
    """
    Проверяет доступность всех изображений продуктов в S3.
    Доступно только для администраторов.
    """
    # Если запрос на страницу HTML
    if request.GET.get('format') != 'json':
        return render(request, 'products/debug_s3_images.html')
        
    results = []
    
    # Получаем все изображения продуктов
    images = ProductImage.objects.all()[:20]  # Ограничиваем 20 для быстрого ответа
    
    for img in images:
        try:
            # Получаем URL
            direct_url = img.get_direct_s3_url()
            
            # Проверяем доступность
            exists = check_s3_file_exists(direct_url)
            
            results.append({
                'product_id': img.product_id,
                'product_name': img.product.name,
                'image_id': img.id,
                'image_name': img.image.name,
                'direct_url': direct_url,
                'exists': exists
            })
        except Exception as e:
            results.append({
                'product_id': img.product_id,
                'image_id': img.id,
                'error': str(e)
            })
    
    # Возвращаем информацию в JSON
    return JsonResponse({
        'count': len(results),
        'results': results,
        'bucket': settings.AWS_STORAGE_BUCKET_NAME,
        's3_endpoint': settings.AWS_S3_ENDPOINT_URL,
        'direct_storage_url': getattr(settings, 'SELECTEL_DIRECT_STORAGE_URL', None)
    })
    
@staff_member_required
def test_s3_images(request):
    """
    Страница для тестирования URL изображений из Selectel S3
    """
    context = {
        'selectel_direct_storage_url': getattr(settings, 'SELECTEL_DIRECT_STORAGE_URL', None),
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'endpoint_url': settings.AWS_S3_ENDPOINT_URL,
    }
    return render(request, 'products/test_s3_images.html', context)

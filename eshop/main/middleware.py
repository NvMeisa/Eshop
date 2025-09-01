import time

from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin


class PerformanceMiddleware(MiddlewareMixin):
    """Middleware для мониторинга производительности"""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response['X-Request-Time'] = str(duration)
            
            # Логируем медленные запросы (> 1 секунды)
            if duration > 1.0:
                print(f"Медленный запрос: {request.path} - {duration:.2f}s")
        
        return response


class CacheMiddleware(MiddlewareMixin):
    """Middleware для кэширования часто запрашиваемых данных"""
    
    def process_request(self, request):
        # Кэшируем категории для всех страниц
        if not hasattr(request, 'cached_categories'):
            categories = cache.get('categories_all')
            if categories is None:
                from .models import Category
                categories = Category.objects.all()
                cache.set('categories_all', categories, 3600)
            request.cached_categories = categories
        
        return None


class SecurityMiddleware(MiddlewareMixin):
    """Middleware для улучшения безопасности"""
    
    def process_response(self, request, response):
        # Добавляем заголовки безопасности
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Ограничиваем размер загружаемых файлов
        if request.method == 'POST' and request.content_type and 'multipart' in request.content_type:
            content_length = request.META.get('CONTENT_LENGTH', 0)
            if content_length and int(content_length) > 5 * 1024 * 1024:  # 5MB
                from django.http import HttpResponse
                return HttpResponse('Файл слишком большой', status=413)
        
        return response

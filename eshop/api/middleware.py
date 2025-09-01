"""
Middleware для API
"""

import logging
import time

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования API запросов
    """

    def process_request(self, request):
        """Обработка входящего запроса"""
        if self._is_api_request(request):
            request.start_time = time.time()
            request.api_request = True

            # Логируем входящий запрос
            logger.info(
                f'API Request: {request.method} {request.path}',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'user': request.user.username
                    if request.user.is_authenticated
                    else 'anonymous',
                    'ip': self._get_client_ip(request),
                },
            )

    def process_response(self, request, response):
        """Обработка исходящего ответа"""
        if hasattr(request, 'api_request') and request.api_request:
            # Вычисляем время выполнения
            duration = time.time() - request.start_time

            # Логируем ответ
            logger.info(
                f'API Response: {request.method} {request.path} - {response.status_code} ({duration:.3f}s)',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'user': request.user.username
                    if request.user.is_authenticated
                    else 'anonymous',
                },
            )

            # Добавляем заголовки с метриками
            response['X-API-Response-Time'] = f'{duration:.3f}s'
            response['X-API-Version'] = self._get_api_version(request)

        return response

    def _is_api_request(self, request):
        """Проверка, является ли запрос API запросом"""
        return request.path.startswith('/api/')

    def _get_client_ip(self, request):
        """Получение IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_api_version(self, request):
        """Получение версии API из пути"""
        path_parts = request.path.split('/')
        if len(path_parts) > 2 and path_parts[1] == 'api':
            return path_parts[2] if len(path_parts) > 2 else 'v1'
        return 'v1'


class APIErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware для обработки ошибок API
    """

    def process_exception(self, request, exception):
        """Обработка исключений"""
        if self._is_api_request(request):
            # Логируем ошибку
            logger.error(
                f'API Error: {request.method} {request.path}',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'error': str(exception),
                    'error_type': type(exception).__name__,
                    'user': request.user.username
                    if request.user.is_authenticated
                    else 'anonymous',
                },
                exc_info=True,
            )

            # Возвращаем JSON ответ с ошибкой
            return JsonResponse(
                {
                    'error': 'Internal Server Error',
                    'message': str(exception)
                    if settings.DEBUG
                    else 'Something went wrong',
                    'status_code': 500,
                    'path': request.path,
                    'method': request.method,
                },
                status=500,
            )

        return None

    def _is_api_request(self, request):
        """Проверка, является ли запрос API запросом"""
        return request.path.startswith('/api/')


class APIRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware для ограничения скорости API запросов
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.request_counts = {}
        self.last_reset = time.time()

    def process_request(self, request):
        """Обработка входящего запроса с проверкой лимитов"""
        if self._is_api_request(request):
            # Сбрасываем счетчики каждый час
            current_time = time.time()
            if current_time - self.last_reset > 3600:
                self.request_counts.clear()
                self.last_reset = current_time

            # Получаем ключ для пользователя
            user_key = self._get_user_key(request)

            # Проверяем лимиты
            if not self._check_rate_limit(user_key, request):
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'message': 'Too many requests. Please try again later.',
                        'status_code': 429,
                    },
                    status=429,
                )

    def _is_api_request(self, request):
        """Проверка, является ли запрос API запросом"""
        return request.path.startswith('/api/')

    def _get_user_key(self, request):
        """Получение ключа пользователя для ограничений"""
        if request.user.is_authenticated:
            return f'user_{request.user.id}'
        else:
            ip = self._get_client_ip(request)
            return f'ip_{ip}'

    def _get_client_ip(self, request):
        """Получение IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _check_rate_limit(self, user_key, request):
        """Проверка лимита запросов"""
        current_time = time.time()

        if user_key not in self.request_counts:
            self.request_counts[user_key] = []

        # Удаляем старые запросы (старше часа)
        self.request_counts[user_key] = [
            req_time
            for req_time in self.request_counts[user_key]
            if current_time - req_time < 3600
        ]

        # Проверяем лимит
        limit = 1000 if request.user.is_authenticated else 100
        if len(self.request_counts[user_key]) >= limit:
            return False

        # Добавляем текущий запрос
        self.request_counts[user_key].append(current_time)
        return True


class APICacheMiddleware(MiddlewareMixin):
    """
    Middleware для кэширования API ответов
    """

    def process_request(self, request):
        """Обработка входящего запроса с проверкой кэша"""
        if self._is_api_request(request) and request.method == 'GET':
            # Здесь можно добавить логику кэширования
            # Например, проверка кэша Redis
            pass

    def process_response(self, request, response):
        """Обработка исходящего ответа с кэшированием"""
        if self._is_api_request(request) and request.method == 'GET':
            # Добавляем заголовки кэширования
            response['Cache-Control'] = 'public, max-age=300'  # 5 минут
            response['Vary'] = 'Accept, Accept-Language'

        return response

    def _is_api_request(self, request):
        """Проверка, является ли запрос API запросом"""
        return request.path.startswith('/api/')

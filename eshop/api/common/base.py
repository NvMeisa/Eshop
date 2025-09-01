"""
Базовые классы для API
"""
from typing import Any, Dict, List

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.response import Response


class BaseViewSet(viewsets.ModelViewSet):
    """
    Базовый ViewSet с общей функциональностью
    """

    def get_queryset(self) -> QuerySet:
        """Получение queryset с оптимизацией"""
        queryset = super().get_queryset()

        # Автоматическое применение select_related для связанных полей
        if hasattr(self, 'select_related_fields'):
            queryset = queryset.select_related(*self.select_related_fields)

        # Автоматическое применение prefetch_related для связанных полей
        if hasattr(self, 'prefetch_related_fields'):
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)

        return queryset

    def get_serializer_context(self) -> Dict[str, Any]:
        """Добавление контекста к сериализатору"""
        context = super().get_serializer_context()
        context['request'] = self.request
        context['view'] = self
        return context

    def handle_exception(self, exc: Exception) -> Response:
        """Обработка исключений с логированием"""
        # Здесь можно добавить логирование
        return super().handle_exception(exc)


class ReadOnlyViewSet(BaseViewSet):
    """
    ViewSet только для чтения
    """
    http_method_names = ['get', 'head', 'options']


class BaseAPIView:
    """
    Базовый класс для API представлений
    """

    def get_response_data(self, data: Any, message: str = None,
                         status_code: int = status.HTTP_200_OK) -> Response:
        """Стандартизированный ответ API"""
        response_data = {
            'success': status_code < 400,
            'data': data,
            'message': message
        }

        if status_code >= 400:
            response_data['error'] = data
            response_data['data'] = None

        return Response(response_data, status=status_code)

    def get_paginated_response(self, data: List[Any],
                              page: int = 1,
                              page_size: int = 20) -> Response:
        """Пагинированный ответ"""
        start = (page - 1) * page_size
        end = start + page_size

        paginated_data = {
            'results': data[start:end],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': len(data),
                'total_pages': (len(data) + page_size - 1) // page_size,
                'has_next': end < len(data),
                'has_previous': page > 1
            }
        }

        return Response(paginated_data)

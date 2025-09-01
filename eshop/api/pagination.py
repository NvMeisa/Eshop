"""
Система пагинации для API
"""

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from rest_framework.pagination import (
    CursorPagination,
    LimitOffsetPagination,
    PageNumberPagination,
)
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Стандартная пагинация по страницам
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response(
            {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data,
                'page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'page_size': self.page_size,
            }
        )


class LimitOffsetPagination(LimitOffsetPagination):
    """
    Пагинация по лимиту и смещению
    """

    default_limit = 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100

    def get_paginated_response(self, data):
        return Response(
            {
                'count': self.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data,
                'limit': self.limit,
                'offset': self.offset,
            }
        )


class CursorPagination(CursorPagination):
    """
    Пагинация по курсору для больших наборов данных
    """

    page_size = 20
    ordering = '-created'
    cursor_query_param = 'cursor'

    def get_paginated_response(self, data):
        return Response(
            {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data,
                'page_size': self.page_size,
            }
        )


class CustomPagination:
    """
    Кастомная пагинация с гибкими настройками
    """

    def __init__(self, page_size=20, max_page_size=100):
        self.page_size = page_size
        self.max_page_size = max_page_size

    def paginate_queryset(self, queryset, request):
        """Пагинация queryset"""
        page = request.query_params.get('page', 1)
        page_size = min(
            int(request.query_params.get('page_size', self.page_size)),
            self.max_page_size,
        )

        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        paginator = Paginator(queryset, page_size)

        try:
            queryset = paginator.page(page)
        except (EmptyPage, PageNotAnInteger):
            queryset = paginator.page(1)

        return queryset, paginator

    def get_paginated_response(self, data, queryset, paginator):
        """Формирование ответа с пагинацией"""
        return Response(
            {
                'count': paginator.count,
                'next': self._get_next_link(queryset),
                'previous': self._get_previous_link(queryset),
                'results': data,
                'page': queryset.number,
                'total_pages': paginator.num_pages,
                'page_size': paginator.per_page,
            }
        )

    def _get_next_link(self, queryset):
        """Получение ссылки на следующую страницу"""
        if not queryset.has_next():
            return None
        return f'?page={queryset.next_page_number()}'

    def _get_previous_link(self, queryset):
        """Получение ссылки на предыдущую страницу"""
        if not queryset.has_previous():
            return None
        return f'?page={queryset.previous_page_number()}'

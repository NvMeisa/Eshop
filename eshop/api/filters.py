"""
Система фильтрации для API
"""
from typing import Any, Dict, List

from django.db.models import Q
from django_filters import rest_framework as filters


class BaseFilterSet(filters.FilterSet):
    """
    Базовый класс для фильтров
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_custom_filters()

    def _setup_custom_filters(self):
        """Настройка кастомных фильтров"""
        pass

    def filter_queryset(self, queryset):
        """Фильтрация queryset с логированием"""
        filtered_queryset = super().filter_queryset(queryset)
        # Здесь можно добавить логирование фильтрации
        return filtered_queryset


class ProductFilter(BaseFilterSet):
    """
    Фильтр для товаров
    """
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = filters.NumberFilter(field_name='category__id')
    available = filters.BooleanFilter()
    created_after = filters.DateFilter(field_name='created', lookup_expr='gte')
    created_before = filters.DateFilter(field_name='created', lookup_expr='lte')

    class Meta:
        model = None  # Будет установлено при использовании
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'category': ['exact'],
            'available': ['exact'],
            'created': ['exact', 'gte', 'lte']
        }

    def filter_available(self, queryset, name, value):
        """Фильтр по доступности"""
        if value is not None:
            return queryset.filter(available=value)
        return queryset

    def filter_price_range(self, queryset, name, value):
        """Фильтр по диапазону цен"""
        if value:
            return queryset.filter(price__range=value)
        return queryset


class CategoryFilter(BaseFilterSet):
    """
    Фильтр для категорий
    """
    name = filters.CharFilter(lookup_expr='icontains')
    has_products = filters.BooleanFilter(method='filter_has_products')

    class Meta:
        model = None
        fields = ['name', 'slug']

    def filter_has_products(self, queryset, name, value):
        """Фильтр по наличию товаров"""
        if value is not None:
            if value:
                return queryset.filter(products__isnull=False).distinct()
            else:
                return queryset.filter(products__isnull=True)
        return queryset


class SearchFilter:
    """
    Универсальный фильтр поиска
    """

    def __init__(self, search_fields: List[str], model_fields: Dict[str, str] = None):
        self.search_fields = search_fields
        self.model_fields = model_fields or {}

    def filter(self, queryset, search_term: str) -> Any:
        """Фильтрация по поисковому запросу"""
        if not search_term:
            return queryset

        q_objects = Q()

        for field in self.search_fields:
            if field in self.model_fields:
                lookup = self.model_fields[field]
                q_objects |= Q(**{lookup: search_term})
            else:
                q_objects |= Q(**{f"{field}__icontains": search_term})

        return queryset.filter(q_objects)

    def filter_with_weights(self, queryset, search_term: str,
                           field_weights: Dict[str, int] = None) -> Any:
        """Фильтрация с весами полей"""
        if not search_term:
            return queryset

        # Простая реализация с весами
        # В реальном проекте можно использовать полнотекстовый поиск
        return self.filter(queryset, search_term)


class AdvancedFilter:
    """
    Продвинутый фильтр с поддержкой сложных запросов
    """

    def __init__(self):
        self.filters = {}

    def add_filter(self, name: str, filter_func):
        """Добавление фильтра"""
        self.filters[name] = filter_func

    def apply_filters(self, queryset, filter_params: Dict[str, Any]) -> Any:
        """Применение всех фильтров"""
        for name, value in filter_params.items():
            if name in self.filters and value is not None:
                queryset = self.filters[name](queryset, value)
        return queryset

    def get_filter_description(self) -> Dict[str, str]:
        """Получение описания доступных фильтров"""
        return {name: func.__doc__ or f"Filter: {name}"
                for name, func in self.filters.items()}

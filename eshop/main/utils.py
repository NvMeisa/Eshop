import hashlib
import json

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q


def generate_cache_key(prefix, *args, **kwargs):
    """Генерация уникального ключа кэша"""
    key_parts = [prefix] + [str(arg) for arg in args]
    
    if kwargs:
        # Сортируем kwargs для стабильности ключа
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
    
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_query_result(cache_key, queryset, timeout=300):
    """Кэширование результата запроса"""
    result = cache.get(cache_key)
    if result is None:
        result = list(queryset)
        cache.set(cache_key, result, timeout)
    return result


def get_paginated_results(queryset, page, per_page=12):
    """Получение пагинированных результатов"""
    paginator = Paginator(queryset, per_page)
    try:
        return paginator.page(page)
    except (ValueError, TypeError):
        return paginator.page(1)


def search_products_optimized(query, category=None, limit=None):
    """Оптимизированный поиск товаров"""
    from .models import Product
    
    # Создаем базовый queryset
    queryset = Product.objects.select_related('category').filter(available=True)
    
    # Добавляем фильтры
    if query:
        # Используем Q объекты для сложных запросов
        search_filters = Q(name__icontains=query) | Q(description__icontains=query)
        queryset = queryset.filter(search_filters)
    
    if category:
        queryset = queryset.filter(category=category)
    
    # Оптимизируем сортировку
    queryset = queryset.order_by('name')
    
    if limit:
        queryset = queryset[:limit]
    
    return queryset


def invalidate_related_cache(model_instance):
    """Инвалидация связанного кэша"""
    if hasattr(model_instance, 'category'):
        # Инвалидируем кэш категории
        cache.delete(f'category_products_{model_instance.category.id}')
        cache.delete('featured_products')
    
    # Инвалидируем общий кэш товаров
    cache.delete('products_all')
    cache.delete('search_results')


def get_cached_categories():
    """Получение кэшированных категорий"""
    cache_key = 'categories_all'
    categories = cache.get(cache_key)
    
    if categories is None:
        from .models import Category
        categories = list(Category.objects.all())
        cache.set(cache_key, categories, 3600)  # 1 час
    
    return categories


def get_cached_featured_products(limit=8):
    """Получение кэшированных популярных товаров"""
    cache_key = f'featured_products_{limit}'
    products = cache.get(cache_key)
    
    if products is None:
        from .models import Product
        products = list(Product.objects.select_related('category').filter(
            available=True
        ).order_by('-created')[:limit])
        cache.set(cache_key, products, 1800)  # 30 минут
    
    return products


def optimize_image_upload(image_field):
    """Оптимизация загрузки изображений"""
    if image_field:
        # Здесь можно добавить логику оптимизации изображений
        # Например, изменение размера, сжатие и т.д.
        pass
    return image_field


def get_product_stats():
    """Получение статистики товаров"""
    cache_key = 'product_stats'
    stats = cache.get(cache_key)
    
    if stats is None:
        from .models import Category, Product
        stats = {
            'total_products': Product.objects.filter(available=True).count(),
            'total_categories': Category.objects.count(),
            'avg_price': Product.objects.filter(available=True).aggregate(
                avg_price=models.Avg('price')
            )['avg_price'] or 0,
        }
        cache.set(cache_key, stats, 3600)  # 1 час
    
    return stats

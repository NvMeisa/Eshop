"""
ViewSet для API версии 1
"""
from django.db.models import Q
from main.models import Cart, CartItem, Category, Product
from main.serializers import (
    CartItemCreateSerializer,
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    ProductListSerializer,
    ProductSerializer,
    UserProfileSerializer,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..common.base import BaseAPIView, BaseViewSet, ReadOnlyViewSet
from ..filters import CategoryFilter, ProductFilter, SearchFilter
from ..pagination import StandardPagination
from ..versioning import VersionedViewSetMixin


class CategoryViewSet(ReadOnlyViewSet, VersionedViewSetMixin):
    """
    ViewSet для категорий (только чтение)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = StandardPagination
    filterset_class = CategoryFilter
    select_related_fields = []
    prefetch_related_fields = ['products']
    lookup_field = 'slug'
    
    # Теги для документации
    swagger_schema_tags = ['categories']
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Получение товаров конкретной категории"""
        category = self.get_object()
        products = Product.objects.filter(
            category=category, 
            available=True
        ).select_related('category')
        
        # Применяем фильтры
        filter_params = request.query_params.dict()
        if filter_params:
            product_filter = ProductFilter(data=filter_params, queryset=products)
            products = product_filter.qs
        
        # Пагинация
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        
        serializer = ProductListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProductViewSet(ReadOnlyViewSet, VersionedViewSetMixin):
    """
    ViewSet для товаров (только чтение)
    """
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductSerializer
    pagination_class = StandardPagination
    filterset_class = ProductFilter
    select_related_fields = ['category']
    prefetch_related_fields = []
    lookup_field = 'slug'
    
    # Теги для документации
    swagger_schema_tags = ['products']
    
    def get_queryset(self):
        """Получение queryset с оптимизацией"""
        queryset = super().get_queryset()
        
        # Поиск
        search_term = self.request.query_params.get('search')
        if search_term:
            search_filter = SearchFilter(['name', 'description'])
            queryset = search_filter.filter(queryset, search_term)
        
        return queryset
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Расширенный поиск товаров"""
        search_term = request.query_params.get('query', '')
        category_id = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        queryset = self.get_queryset()
        
        # Поиск по тексту
        if search_term:
            search_filter = SearchFilter(['name', 'description'])
            queryset = search_filter.filter(queryset, search_term)
        
        # Фильтр по категории
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Фильтр по цене
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Пагинация
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = ProductListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """Получение связанных товаров"""
        product = self.get_object()
        related_products = Product.objects.filter(
            category=product.category,
            available=True
        ).exclude(id=product.id)[:4]
        
        serializer = ProductListSerializer(related_products, many=True)
        return Response(serializer.data)


class CartViewSet(BaseViewSet, VersionedViewSetMixin):
    """
    ViewSet для корзины
    """
    serializer_class = CartSerializer
    pagination_class = StandardPagination
    select_related_fields = ['user']
    prefetch_related_fields = ['items__product', 'items__product__category']
    
    # Теги для документации
    swagger_schema_tags = ['carts']
    
    def get_queryset(self):
        """Получение корзин только для текущего пользователя"""
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        return Cart.objects.none()
    
    def perform_create(self, serializer):
        """Создание корзины для текущего пользователя"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Добавление товара в корзину"""
        cart = self.get_object()
        serializer = CartItemCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            
            try:
                product = Product.objects.get(id=product_id, available=True)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Товар не найден или недоступен'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Проверяем, есть ли уже такой товар в корзине
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                if cart_item.quantity > 99:
                    cart_item.quantity = 99
                cart_item.save()
            
            # Возвращаем обновленную корзину
            cart_serializer = CartSerializer(cart)
            return Response(cart_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Очистка корзины"""
        cart = self.get_object()
        cart.items.all().delete()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Получение сводки корзины"""
        cart = self.get_object()
        return Response({
            'total_items': cart.total_items,
            'total_price': cart.total_price,
            'items_count': cart.items.count()
        })


class CartItemViewSet(BaseViewSet, VersionedViewSetMixin):
    """
    ViewSet для товаров в корзине
    """
    serializer_class = CartItemSerializer
    pagination_class = StandardPagination
    select_related_fields = ['cart', 'product']
    prefetch_related_fields = ['product__category']
    
    # Теги для документации
    swagger_schema_tags = ['cart-items']
    
    def get_queryset(self):
        """Получение товаров корзины только для текущего пользователя"""
        if self.request.user.is_authenticated:
            return CartItem.objects.filter(cart__user=self.request.user)
        return CartItem.objects.none()
    
    def perform_update(self, serializer):
        """Обновление товара в корзине"""
        instance = serializer.instance
        quantity = serializer.validated_data.get('quantity', instance.quantity)
        
        if quantity < 1:
            instance.delete()
        else:
            instance.quantity = quantity
            instance.save()
    
    @action(detail=True, methods=['post'])
    def increment(self, request, pk=None):
        """Увеличение количества товара"""
        cart_item = self.get_object()
        cart_item.quantity += 1
        if cart_item.quantity > 99:
            cart_item.quantity = 99
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def decrement(self, request, pk=None):
        """Уменьшение количества товара"""
        cart_item = self.get_object()
        cart_item.quantity -= 1
        
        if cart_item.quantity < 1:
            cart_item.delete()
            return Response({'message': 'Товар удален из корзины'})
        
        cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)


class UserProfileViewSet(ReadOnlyViewSet, VersionedViewSetMixin):
    """
    ViewSet для профиля пользователя
    """
    serializer_class = UserProfileSerializer
    pagination_class = StandardPagination
    select_related_fields = []
    prefetch_related_fields = ['cart_set']
    
    # Теги для документации
    swagger_schema_tags = ['profile']
    
    def get_queryset(self):
        """Получение профиля только для текущего пользователя"""
        if self.request.user.is_authenticated:
            from django.contrib.auth.models import User
            return User.objects.filter(id=self.request.user.id)
        return User.objects.none()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получение профиля текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def orders(self, request):
        """Получение истории заказов пользователя"""
        # Здесь можно добавить логику для заказов
        return Response({'message': 'История заказов пока не реализована'})

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(
        max_length=120, db_index=True, verbose_name='Название'
    )
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:product_list_by_category', args=[self.slug])
    
    @classmethod
    def get_all_cached(cls):
        """Получение всех категорий с кэшированием"""
        cache_key = 'categories_all'
        categories = cache.get(cache_key)
        if categories is None:
            categories = cls.objects.all()
            cache.set(cache_key, categories, 3600)  # 1 час
        return categories


class Product(models.Model):
    name = models.CharField(
        max_length=120, verbose_name='Название', db_index=True
    )
    slug = models.SlugField(max_length=120, unique=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category, related_name='products', on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        indexes = [
            models.Index(fields=['available']),
            models.Index(fields=['price']),
            models.Index(fields=['created']),
            models.Index(fields=['category', 'available']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:product_detail', args=[self.id, self.slug])
    
    @classmethod
    def get_featured_products(cls, limit=8):
        """Получение популярных товаров с кэшированием"""
        cache_key = 'featured_products'
        products = cache.get(cache_key)
        if products is None:
            products = cls.objects.select_related('category').filter(
                available=True
            ).order_by('-created')[:limit]
            cache.set(cache_key, products, 1800)  # 30 минут
        return products
    
    @classmethod
    def search_products(cls, query, category=None):
        """Поиск товаров с оптимизацией"""
        queryset = cls.objects.select_related('category').filter(available=True)
        
        if query:
            queryset = queryset.filter(
                models.Q(name__icontains=query) | 
                models.Q(description__icontains=query)
            )
        
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        if self.user:
            return f"Корзина пользователя {self.user.username}"
        return f"Корзина сессии {self.session_key}"

    @property
    def total_price(self):
        """Общая стоимость корзины с кэшированием"""
        cache_key = f'cart_total_{self.id}'
        total = cache.get(cache_key)
        if total is None:
            total = sum(item.total_price for item in self.items.all())
            cache.set(cache_key, total, 300)  # 5 минут
        return total

    @property
    def total_items(self):
        """Общее количество товаров в корзине с кэшированием"""
        cache_key = f'cart_items_{self.id}'
        total = cache.get(cache_key)
        if total is None:
            total = sum(item.quantity for item in self.items.all())
            cache.set(cache_key, total, 300)  # 5 минут
        return total
    
    def clear_cache(self):
        """Очистка кэша корзины"""
        cache.delete(f'cart_total_{self.id}')
        cache.delete(f'cart_items_{self.id}')


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        unique_together = ('cart', 'product')
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price
    
    def save(self, *args, **kwargs):
        """Переопределяем save для очистки кэша"""
        super().save(*args, **kwargs)
        self.cart.clear_cache()
    
    def delete(self, *args, **kwargs):
        """Переопределяем delete для очистки кэша"""
        cart = self.cart
        super().delete(*args, **kwargs)
        cart.clear_cache()

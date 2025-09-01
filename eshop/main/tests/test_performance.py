"""
Тесты производительности для проверки оптимизации
"""
import time

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection, reset_queries
from django.test import Client, TestCase
from django.urls import reverse
from main.models import Cart, CartItem, Category, Product


class PerformanceTestCase(TestCase):
    """Тесты производительности"""

    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Создаем категории
        self.category1 = Category.objects.create(
            name='Электроника',
            slug='electronics'
        )
        self.category2 = Category.objects.create(
            name='Одежда',
            slug='clothing'
        )
        
        # Создаем товары
        for i in range(50):
            category = self.category1 if i % 2 == 0 else self.category2
            Product.objects.create(
                name=f'Товар {i}',
                slug=f'product-{i}',
                description=f'Описание товара {i}',
                price=100.00 + i,
                available=True,
                category=category
            )
        
        # Создаем корзину
        self.cart = Cart.objects.create(user=self.user)
        
        # Добавляем товары в корзину
        for i in range(5):
            product = Product.objects.get(id=i+1)
            CartItem.objects.create(
                cart=self.cart,
                product=product,
                quantity=i+1
            )
        
        self.client = Client()
        self.client.force_login(self.user)

    def test_index_page_performance(self):
        """Тест производительности главной страницы"""
        start_time = time.time()
        
        # Очищаем кэш для чистого теста
        cache.clear()
        
        # Первый запрос (без кэша)
        response1 = self.client.get(reverse('main:index'))
        first_request_time = time.time() - start_time
        
        # Второй запрос (с кэшем)
        start_time = time.time()
        response2 = self.client.get(reverse('main:index'))
        second_request_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Второй запрос должен быть быстрее
        self.assertLess(second_request_time, first_request_time)
        
        print(f"⏱️  Первый запрос: {first_request_time:.3f}s")
        print(f"⏱️  Второй запрос: {second_request_time:.3f}s")
        print(f"🚀 Ускорение: {first_request_time/second_request_time:.1f}x")

    def test_product_list_performance(self):
        """Тест производительности списка товаров"""
        reset_queries()
        
        response = self.client.get(reverse('main:product_list'))
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем количество SQL запросов
        query_count = len(connection.queries)
        print(f"🔍 SQL запросов для списка товаров: {query_count}")
        
        # Должно быть не более 3-4 запросов
        self.assertLessEqual(query_count, 4)

    def test_search_performance(self):
        """Тест производительности поиска"""
        start_time = time.time()
        
        response = self.client.get(
            reverse('main:search_api'),
            {'q': 'электроника'}
        )
        
        search_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(search_time, 0.1)  # Поиск должен быть быстрее 100ms
        
        print(f"🔍 Время поиска: {search_time:.3f}s")

    def test_cart_performance(self):
        """Тест производительности корзины"""
        reset_queries()
        
        response = self.client.get(reverse('main:cart'))
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем количество SQL запросов
        query_count = len(connection.queries)
        print(f"🛒 SQL запросов для корзины: {query_count}")
        
        # Должно быть не более 2-3 запросов
        self.assertLessEqual(query_count, 3)

    def test_cache_efficiency(self):
        """Тест эффективности кэширования"""
        # Очищаем кэш
        cache.clear()
        
        # Первый запрос - без кэша
        start_time = time.time()
        response1 = self.client.get(reverse('main:index'))
        first_time = time.time() - start_time
        
        # Второй запрос - с кэшем
        start_time = time.time()
        response2 = self.client.get(reverse('main:index'))
        second_time = time.time() - start_time
        
        # Проверяем, что кэш работает
        self.assertLess(second_time, first_time)
        
        # Кэш должен давать минимум 2x ускорение
        speedup = first_time / second_time
        self.assertGreaterEqual(speedup, 2.0)
        
        print(f"🚀 Ускорение от кэша: {speedup:.1f}x")

    def test_database_indexes(self):
        """Тест эффективности индексов"""
        # Тест поиска по slug (должен использовать индекс)
        start_time = time.time()
        category = Category.objects.get(slug='electronics')
        slug_search_time = time.time() - start_time
        
        # Тест поиска по name (должен использовать индекс)
        start_time = time.time()
        category = Category.objects.get(name='Электроника')
        name_search_time = time.time() - start_time
        
        # Оба поиска должны быть быстрыми
        self.assertLess(slug_search_time, 0.01)
        self.assertLess(name_search_time, 0.01)
        
        print(f"🔍 Поиск по slug: {slug_search_time:.4f}s")
        print(f"🔍 Поиск по name: {name_search_time:.4f}s")

    def test_pagination_performance(self):
        """Тест производительности пагинации"""
        # Тестируем разные страницы
        for page in [1, 2, 3]:
            start_time = time.time()
            response = self.client.get(
                reverse('main:product_list'),
                {'page': page}
            )
            page_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(page_time, 0.1)  # Каждая страница должна загружаться быстро
            
            print(f"📄 Страница {page}: {page_time:.3f}s")

    def tearDown(self):
        """Очистка после тестов"""
        cache.clear()
        super().tearDown()


class CacheTestCase(TestCase):
    """Тесты кэширования"""

    def setUp(self):
        """Подготовка тестовых данных"""
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )

    def test_category_caching(self):
        """Тест кэширования категорий"""
        # Очищаем кэш
        cache.clear()
        
        # Первый вызов - без кэша
        start_time = time.time()
        categories1 = Category.get_all_cached()
        first_time = time.time() - start_time
        
        # Второй вызов - с кэшем
        start_time = time.time()
        categories2 = Category.get_all_cached()
        second_time = time.time() - start_time
        
        # Результаты должны быть одинаковыми
        self.assertEqual(len(categories1), len(categories2))
        
        # Второй вызов должен быть быстрее
        self.assertLess(second_time, first_time)
        
        print(f"⏱️  Первый вызов: {first_time:.4f}s")
        print(f"⏱️  Второй вызов: {second_time:.4f}s")

    def test_product_caching(self):
        """Тест кэширования товаров"""
        # Создаем тестовые товары
        for i in range(10):
            Product.objects.create(
                name=f'Тестовый товар {i}',
                slug=f'test-product-{i}',
                price=100.00,
                available=True,
                category=self.category
            )
        
        # Очищаем кэш
        cache.clear()
        
        # Первый вызов - без кэша
        start_time = time.time()
        products1 = Product.get_featured_products(5)
        first_time = time.time() - start_time
        
        # Второй вызов - с кэшем
        start_time = time.time()
        products2 = Product.get_featured_products(5)
        second_time = time.time() - start_time
        
        # Результаты должны быть одинаковыми
        self.assertEqual(len(products1), len(products2))
        
        # Второй вызов должен быть быстрее
        self.assertLess(second_time, first_time)
        
        print(f"⏱️  Первый вызов: {first_time:.4f}s")
        print(f"⏱️  Второй вызов: {second_time:.4f}s")

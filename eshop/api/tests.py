"""
Тесты для API приложения
"""

import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from main.models import Cart, CartItem, Category, Product
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class APIBaseTestCase(APITestCase):
    """
    Базовый класс для тестов API
    """

    def setUp(self):
        """Настройка тестов"""
        self.client = APIClient()

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )

        # Создаем тестовую категорию
        self.category = Category.objects.create(
            name='Test Category', slug='test-category'
        )

        # Создаем тестовый товар
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test Description',
            price=100.00,
            category=self.category,
            available=True,
        )

        # Создаем тестовую корзину
        self.cart = Cart.objects.create(user=self.user)

    def authenticate_user(self):
        """Аутентификация пользователя"""
        self.client.force_authenticate(user=self.user)


class CategoryAPITestCase(APIBaseTestCase):
    """
    Тесты для API категорий
    """

    def test_category_list(self):
        """Тест получения списка категорий"""
        url = reverse('api-v1:category-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_category_detail(self):
        """Тест получения детальной информации о категории"""
        url = reverse(
            'api-v1:category-detail', kwargs={'slug': self.category.slug}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.category.name)
        self.assertEqual(response.data['slug'], self.category.slug)

    def test_category_products(self):
        """Тест получения товаров категории"""
        url = reverse(
            'api-v1:category-products', kwargs={'slug': self.category.slug}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)


class ProductAPITestCase(APIBaseTestCase):
    """
    Тесты для API товаров
    """

    def test_product_list(self):
        """Тест получения списка товаров"""
        url = reverse('api-v1:product-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_product_detail(self):
        """Тест получения детальной информации о товаре"""
        url = reverse(
            'api-v1:product-detail', kwargs={'slug': self.product.slug}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.product.name)
        self.assertEqual(response.data['price'], str(self.product.price))

    def test_product_search(self):
        """Тест поиска товаров"""
        url = reverse('api-v1:product-search')
        response = self.client.get(url, {'query': 'Test'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_product_related(self):
        """Тест получения связанных товаров"""
        # Создаем еще один товар в той же категории
        Product.objects.create(
            name='Related Product',
            slug='related-product',
            description='Related Description',
            price=150.00,
            category=self.category,
            available=True,
        )

        url = reverse(
            'api-v1:product-related', kwargs={'slug': self.product.slug}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class CartAPITestCase(APIBaseTestCase):
    """
    Тесты для API корзины
    """

    def setUp(self):
        """Дополнительная настройка для тестов корзины"""
        super().setUp()
        self.authenticate_user()

    def test_cart_list(self):
        """Тест получения списка корзин пользователя"""
        url = reverse('api-v1:cart-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_cart_create(self):
        """Тест создания корзины"""
        # Удаляем существующую корзину
        Cart.objects.filter(user=self.user).delete()

        url = reverse('api-v1:cart-list')
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)

    def test_cart_add_item(self):
        """Тест добавления товара в корзину"""
        url = reverse('api-v1:cart-add-item', kwargs={'pk': self.cart.pk})
        data = {'product_id': self.product.id, 'quantity': 2}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 1)
        self.assertEqual(CartItem.objects.get(cart=self.cart).quantity, 2)

    def test_cart_clear(self):
        """Тест очистки корзины"""
        # Добавляем товар в корзину
        CartItem.objects.create(
            cart=self.cart, product=self.product, quantity=1
        )

        url = reverse('api-v1:cart-clear', kwargs={'pk': self.cart.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)

    def test_cart_summary(self):
        """Тест получения сводки корзины"""
        # Добавляем товар в корзину
        CartItem.objects.create(
            cart=self.cart, product=self.product, quantity=2
        )

        url = reverse('api-v1:cart-summary', kwargs={'pk': self.cart.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_items', response.data)
        self.assertIn('total_price', response.data)
        self.assertEqual(response.data['items_count'], 1)


class CartItemAPITestCase(APIBaseTestCase):
    """
    Тесты для API товаров в корзине
    """

    def setUp(self):
        """Дополнительная настройка для тестов товаров корзины"""
        super().setUp()
        self.authenticate_user()

        # Создаем товар в корзине
        self.cart_item = CartItem.objects.create(
            cart=self.cart, product=self.product, quantity=1
        )

    def test_cart_item_list(self):
        """Тест получения списка товаров корзины"""
        url = reverse('api-v1:cartitem-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_cart_item_update(self):
        """Тест обновления товара в корзине"""
        url = reverse(
            'api-v1:cartitem-detail', kwargs={'pk': self.cart_item.pk}
        )
        data = {'quantity': 3}
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 3)

    def test_cart_item_increment(self):
        """Тест увеличения количества товара"""
        url = reverse(
            'api-v1:cartitem-increment', kwargs={'pk': self.cart_item.pk}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)

    def test_cart_item_decrement(self):
        """Тест уменьшения количества товара"""
        # Устанавливаем количество 2
        self.cart_item.quantity = 2
        self.cart_item.save()

        url = reverse(
            'api-v1:cartitem-decrement', kwargs={'pk': self.cart_item.pk}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 1)

    def test_cart_item_delete_on_zero(self):
        """Тест удаления товара при нулевом количестве"""
        url = reverse(
            'api-v1:cartitem-decrement', kwargs={'pk': self.cart_item.pk}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(
            CartItem.objects.filter(pk=self.cart_item.pk).count(), 0
        )


class UserProfileAPITestCase(APIBaseTestCase):
    """
    Тесты для API профиля пользователя
    """

    def setUp(self):
        """Дополнительная настройка для тестов профиля"""
        super().setUp()
        self.authenticate_user()

    def test_profile_list(self):
        """Тест получения списка профилей"""
        url = reverse('api-v1:profile-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_profile_me(self):
        """Тест получения профиля текущего пользователя"""
        url = reverse('api-v1:profile-me')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)

    def test_profile_orders(self):
        """Тест получения истории заказов"""
        url = reverse('api-v1:profile-orders')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)


class APIAuthenticationTestCase(APITestCase):
    """
    Тесты аутентификации API
    """

    def setUp(self):
        """Настройка тестов"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )

    def test_anonymous_access_to_public_endpoints(self):
        """Тест доступа анонимных пользователей к публичным эндпоинтам"""
        # Создаем тестовую категорию
        category = Category.objects.create(
            name='Test Category', slug='test-category'
        )

        url = reverse('api-v1:category-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_user_access(self):
        """Тест доступа аутентифицированных пользователей"""
        self.client.force_authenticate(user=self.user)

        # Тест доступа к защищенным эндпоинтам
        url = reverse('api-v1:profile-me')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_denied(self):
        """Тест отказа в доступе неаутентифицированным пользователям"""
        url = reverse('api-v1:profile-me')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

"""
URL маршруты для API версии 1
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Создаем роутер для API v1
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'carts', views.CartViewSet, basename='cart')
router.register(r'cart-items', views.CartItemViewSet, basename='cart-item')
router.register(r'profile', views.UserProfileViewSet, basename='profile')

# URL маршруты для API v1
urlpatterns = [
    # Основные маршруты роутера
    path('', include(router.urls)),
    

    
    # Дополнительные маршруты
    path('search/', views.ProductViewSet.as_view({'get': 'search'}), name='product-search'),
    path('featured/', views.ProductViewSet.as_view({'get': 'list'}), name='featured-products'),
]

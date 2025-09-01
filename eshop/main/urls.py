from django.urls import include, path

from . import views

app_name = 'main'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),  # Главная страница
    path('products/', views.ProductList.as_view(), name='product_list'),  # Список всех товаров
    
    # URL-маршруты для корзины (должны быть ПЕРЕД паттерном категорий)
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Детальная страница товара
    path(
        '<int:pk>/<slug:slug>/',
        views.ProductDetail.as_view(),
        name='product_detail',
    ),
    
    # Список товаров по категории
    path(
        '<slug:category_slug>/',
        views.ProductList.as_view(),
        name='product_list_by_category',
    ),
]

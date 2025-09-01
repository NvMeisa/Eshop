import json

from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView

from .models import Cart, CartItem, Category, Product


# Улучшенный IndexView с кэшированием
@method_decorator(cache_page(60 * 15), name='dispatch')  # Кэшируем на 15 минут
class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Используем методы моделей для кэширования
        context['categories'] = Category.get_all_cached()
        context['featured_products'] = Product.get_featured_products(8)
        return context


class ProductList(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'main/product_list.html'
    paginate_by = 12  # Добавляем пагинацию
    category = None

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug)
            queryset = Product.objects.select_related('category').filter(
                category=self.category, available=True
            )
        else:
            queryset = Product.objects.select_related('category').filter(
                available=True
            )

        # Добавляем поиск по названию
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        # Добавляем сортировку
        sort_by = self.request.GET.get('sort', 'name')
        if sort_by == 'price':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created')
        else:
            queryset = queryset.order_by('name')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Кэшируем категории
        categories = cache.get('categories_all')
        if categories is None:
            categories = Category.objects.all()
            cache.set('categories_all', categories, 3600)

        context['categories'] = categories
        context['category'] = self.category
        context['search_query'] = self.request.GET.get('search', '')
        context['sort_by'] = self.request.GET.get('sort', 'name')
        return context


class ProductDetail(DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'main/product_detail.html'

    def get_queryset(self):
        return Product.objects.select_related('category').filter(
            available=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Кэшируем рекомендуемые товары
        cache_key = f'recommended_products_{product.category.id}_{product.id}'
        recommended_products = cache.get(cache_key)
        if recommended_products is None:
            recommended_products = (
                Product.objects.select_related('category')
                .filter(category=product.category, available=True)
                .exclude(id=product.id)[:4]
            )
            cache.set(cache_key, recommended_products, 1800)

        context['recommended_products'] = recommended_products
        return context


class CartView(TemplateView):
    template_name = 'main/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart()
        if cart:
            # Оптимизируем запрос с prefetch_related
            cart_items = cart.items.select_related('product').all()
            context['cart_items'] = cart_items
            context['total_items'] = cart.total_items
            context['subtotal'] = cart.total_price
            context['total'] = cart.total_price
        else:
            context['cart_items'] = []
            context['total_items'] = 0
            context['subtotal'] = 0
            context['total'] = 0
        return context

    def get_cart(self):
        """Получение корзины с оптимизацией"""
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart


# Миксин для повторяющейся логики корзины
class CartMixin:
    def get_cart(self, request):
        """Получение корзины с оптимизацией"""
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart


@require_POST
def add_to_cart(request, product_id):
    """Добавление товара в корзину с улучшенной валидацией"""
    try:
        # Валидация входных данных
        if not request.body:
            return JsonResponse(
                {'success': False, 'message': 'Отсутствуют данные'}, status=400
            )

        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))

        if quantity < 1:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Количество должно быть больше 0',
                },
                status=400,
            )

        if quantity > 99:  # Ограничиваем максимальное количество
            return JsonResponse(
                {'success': False, 'message': 'Максимальное количество: 99'},
                status=400,
            )

        product = get_object_or_404(Product, id=product_id, available=True)

        # Используем миксин для получения корзины
        cart_mixin = CartMixin()
        cart = cart_mixin.get_cart(request)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > 99:
                cart_item.quantity = 99
            cart_item.save()

        # Инвалидируем кэш корзины
        cache.delete(f'cart_{cart.id}')

        return JsonResponse(
            {
                'success': True,
                'message': f'Товар "{product.name}" добавлен в корзину',
                'cart_total': cart.total_items,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'message': 'Неверный формат данных'}, status=400
        )
    except ValueError:
        return JsonResponse(
            {'success': False, 'message': 'Неверное значение количества'},
            status=400,
        )
    except Exception:
        return JsonResponse(
            {
                'success': False,
                'message': 'Произошла ошибка при добавлении товара',
            },
            status=500,
        )


@require_POST
def update_cart_item(request, item_id):
    """Обновление количества товара в корзине"""
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))

        if quantity < 1:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Количество должно быть больше 0',
                },
                status=400,
            )

        if quantity > 99:
            return JsonResponse(
                {'success': False, 'message': 'Максимальное количество: 99'},
                status=400,
            )

        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.quantity = quantity
        cart_item.save()

        # Инвалидируем кэш корзины
        cache.delete(f'cart_{cart_item.cart.id}')

        return JsonResponse(
            {
                'success': True,
                'message': 'Количество обновлено',
                'new_total': cart_item.cart.total_price,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'message': 'Неверный формат данных'}, status=400
        )
    except ValueError:
        return JsonResponse(
            {'success': False, 'message': 'Неверное значение количества'},
            status=400,
        )
    except Exception:
        return JsonResponse(
            {'success': False, 'message': 'Произошла ошибка при обновлении'},
            status=500,
        )


@require_POST
def remove_cart_item(request, item_id):
    """Удаление товара из корзины"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_id = cart_item.cart.id
        cart_item.delete()

        # Инвалидируем кэш корзины
        cache.delete(f'cart_{cart_id}')

        return JsonResponse(
            {'success': True, 'message': 'Товар удален из корзины'}
        )

    except Exception:
        return JsonResponse(
            {'success': False, 'message': 'Произошла ошибка при удалении'},
            status=500,
        )


@require_POST
def clear_cart(request):
    """Очистка корзины"""
    try:
        cart_mixin = CartMixin()
        cart = cart_mixin.get_cart(request)

        cart.items.all().delete()

        # Инвалидируем кэш корзины
        cache.delete(f'cart_{cart.id}')

        return JsonResponse({'success': True, 'message': 'Корзина очищена'})

    except Exception:
        return JsonResponse(
            {
                'success': False,
                'message': 'Произошла ошибка при очистке корзины',
            },
            status=500,
        )

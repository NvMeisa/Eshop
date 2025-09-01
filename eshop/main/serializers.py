from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Cart, CartItem, Category, Product


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'products_count']
        read_only_fields = ['id']
    
    def get_products_count(self, obj):
        return obj.products.filter(available=True).count()


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для товаров"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'image', 'description', 
            'price', 'available', 'created', 'updated', 
            'category', 'category_id'
        ]
        read_only_fields = ['id', 'created', 'updated']
    
    def validate_price(self, value):
        """Валидация цены"""
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше нуля")
        return value
    
    def validate_name(self, value):
        """Валидация названия"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Название должно содержать минимум 3 символа")
        return value.strip()


class ProductListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка товаров (без детальной информации)"""
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'image', 'price', 'category', 'available']


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товаров в корзине"""
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 'created']
        read_only_fields = ['id', 'created']
    
    def get_total_price(self, obj):
        return obj.total_price
    
    def validate_quantity(self, value):
        """Валидация количества"""
        if value < 1:
            raise serializers.ValidationError("Количество должно быть больше нуля")
        if value > 99:
            raise serializers.ValidationError("Максимальное количество: 99")
        return value


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'total_price', 'created', 'updated']
        read_only_fields = ['id', 'created', 'updated']
    
    def get_total_items(self, obj):
        return obj.total_items
    
    def get_total_price(self, obj):
        return obj.total_price


class CartItemCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания товара в корзине"""
    class Meta:
        model = CartItem
        fields = ['product_id', 'quantity']
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Количество должно быть больше нуля")
        if value > 99:
            raise serializers.ValidationError("Максимальное количество: 99")
        return value


class SearchSerializer(serializers.Serializer):
    """Сериализатор для поиска"""
    query = serializers.CharField(max_length=200, required=False, allow_blank=True)
    category = serializers.IntegerField(required=False)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    available_only = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Валидация данных поиска"""
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise serializers.ValidationError("Минимальная цена не может быть больше максимальной")
        
        return data


class ProductFilterSerializer(serializers.Serializer):
    """Сериализатор для фильтрации товаров"""
    category = serializers.IntegerField(required=False)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    available_only = serializers.BooleanField(default=True)
    sort_by = serializers.ChoiceField(
        choices=[
            ('name', 'По названию'),
            ('price', 'По цене (возрастание)'),
            ('price_desc', 'По цене (убывание)'),
            ('newest', 'По дате добавления'),
            ('oldest', 'По дате добавления (старые)')
        ],
        required=False,
        default='name'
    )


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    carts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'carts_count']
        read_only_fields = ['id', 'date_joined']
    
    def get_carts_count(self, obj):
        return obj.cart_set.count()

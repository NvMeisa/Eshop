from django.contrib import admin

from .models import Cart, CartItem, Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    list_display_links = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'available', 'created', 'updated']
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'total_price', 'total_items', 'created', 'updated']
    list_filter = ['created', 'updated']
    readonly_fields = ['total_price', 'total_items']
    search_fields = ['user__username', 'session_key']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'total_price', 'created']
    list_filter = ['created', 'updated']
    readonly_fields = ['total_price']
    search_fields = ['product__name', 'cart__user__username']

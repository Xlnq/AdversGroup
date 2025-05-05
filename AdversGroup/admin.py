from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin

from djangoProject import settings
from .models import (
    User, Material, Color, Size, Category,
    Product, ProductImage, ProductCategory,
    Cart, CartItem, Order, OrderItem, AuditLog
)

from django.urls import path
from django.template.response import TemplateResponse
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.db.models import Count

from .models import Order, User

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone_number')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

# Админка для материалов
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'density')
    search_fields = ('name',)
    list_per_page = 20

# Админка для цветов
class ColorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    list_per_page = 20

# Админка для размеров
class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'dimensions')
    search_fields = ('dimensions',)
    list_per_page = 20

# Админка для категорий
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',)
    list_per_page = 20

# Inline для изображений товара
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'sort_order', 'is_additional')

# Inline для категорий товара
class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1
    fields = ('category', 'is_primary')

# Админка для товаров
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'material', 'color', 'size', 'created_at')
    list_filter = ('material', 'color', 'size', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ProductImageInline, ProductCategoryInline]
    list_per_page = 20

# Админка для изображений товаров
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'image', 'sort_order', 'is_additional')
    list_filter = ('is_additional',)
    search_fields = ('product__name',)
    list_per_page = 20

# Админка для категорий товаров
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'category', 'is_primary')
    list_filter = ('category', 'is_primary')
    search_fields = ('product__name', 'category__name')
    list_per_page = 20

# Inline для элементов корзины
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'price')

# Админка для корзин
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    search_fields = ('user__username',)
    inlines = [CartItemInline]
    list_per_page = 20

# Админка для элементов корзины
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'price', 'added_at')
    search_fields = ('cart__user__username', 'product__name')
    list_per_page = 20

# Inline для элементов заказа
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'product_name', 'quantity', 'price')

# Админка для заказов
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'user__username', 'contact_phone')
    inlines = [OrderItemInline]
    list_per_page = 20
    readonly_fields = ('order_number', 'created_at', 'updated_at')

# Админка для элементов заказа
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'product_name', 'quantity', 'price')
    search_fields = ('order__order_number', 'product__name', 'product_name')
    list_per_page = 20

# Админка для логов
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'action_type', 'table_name', 'record_id')
    list_filter = ('action_type', 'table_name')
    search_fields = ('user__username', 'table_name')
    readonly_fields = ('action_time', 'user', 'action_type', 'table_name', 'record_id', 'old_values', 'new_values')
    list_per_page = 50

from AdversGroup.models import Order, User

class CustomAdminSite(AdminSite):
    site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Администрирование магазина')
    site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Магазин')
    index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Панель управления')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('statistics/', self.admin_view(self.statistics_view), name='statistics'),
        ]
        return custom_urls + urls

    def statistics_view(self, request):
        orders = (
            Order.objects.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        users = (
            User.objects.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        context = dict(
            self.each_context(request),
            title='Статистика',
            orders_data=list(orders),
            users_data=list(users),
        )
        return TemplateResponse(request, 'admin/statistics.html', context)
custom_admin_site = CustomAdminSite(name='custom_admin')

# Регистрация всех моделей
admin.site.register(User, CustomUserAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Size, SizeAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
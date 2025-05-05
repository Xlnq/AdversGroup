import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import os


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Material(models.Model):
    name = models.CharField(max_length=100, unique=True)
    density = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'materials'
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'colors'
        verbose_name = 'Цвет'
        verbose_name_plural = 'Цвета'


class Size(models.Model):
    dimensions = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = 'sizes'
        verbose_name = 'Размер'
        verbose_name_plural = 'Размеры'


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class Meta:
        db_table = 'categories'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


def product_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"product_{timezone.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('shopper/', filename)


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def main_image(self):
        return self.images.filter(is_additional=False).first()

    class Meta:
        db_table = 'products'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

class ShopperDesign(models.Model):
    PRINTING_METHODS = (
        ('silk', 'Шелкография'),
        ('embroidery', 'Вышивка'),
        ('transfer', 'Полноцвет с трансфером')
    )

    SIDE_CHOICES = (
        ('front', 'Лицевая сторона'),
        ('back', 'Обратная сторона'),
        ('both', 'Обе стороны')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    printing_method = models.CharField(
        max_length=20,
        choices=PRINTING_METHODS,
        default='silk'  # Указываем значение по умолчанию
    )
    printing_side = models.CharField(
        max_length=10,
        choices=SIDE_CHOICES,
        default='front'  # Добавляем значение по умолчанию и для этого поля
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    final_pdf = models.FileField(upload_to='designs/pdf/', null=True, blank=True)
    canvas_width = models.FloatField(null=True, blank=True, help_text="Ширина холста в мм")
    canvas_height = models.FloatField(null=True, blank=True, help_text="Высота холста в мм")

    def save(self, *args, **kwargs):
        if not self.canvas_width or not self.canvas_height:
            # Автозаполнение при создании
            defaults = {
                'silk': (230, 300),
                'embroidery': (170, 170),
                'transfer': (240, 350)
            }.get(self.printing_method, (210, 297))
            self.canvas_width = self.canvas_width or defaults[0]
            self.canvas_height = self.canvas_height or defaults[1]
        super().save(*args, **kwargs)

class DesignElement(models.Model):
    ELEMENT_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('shape', 'Shape'),
    )

    design = models.ForeignKey(ShopperDesign, on_delete=models.CASCADE, related_name='elements')
    element_type = models.CharField(max_length=10, choices=ELEMENT_TYPES)
    side = models.CharField(max_length=10, choices=(('front', 'Front'), ('back', 'Back')))
    content = models.TextField(blank=True, null=True)
    x_position = models.FloatField()
    y_position = models.FloatField()
    width = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    rotation = models.FloatField(default=0)
    color = models.CharField(max_length=20, blank=True, null=True)
    font_family = models.CharField(max_length=50, blank=True, null=True)
    font_size = models.IntegerField(blank=True, null=True)
    z_index = models.IntegerField(default=0)
    opacity = models.FloatField(default=1.0)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to=product_image_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    sort_order = models.IntegerField(default=0)
    is_additional = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.product and self.product.pk is None:
            self.product.save()

        if not self.product.images.exists():
            self.is_additional = False

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'product_images'
        ordering = ['sort_order']
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'

class ProductCategory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_categories'
        unique_together = ('product', 'category')
        verbose_name = 'Категория товара'
        verbose_name_plural = 'Категории товаров'


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carts'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    @property
    def product_image(self):
        return self.product.main_image

    def total_price(self):
        return self.product.price * self.quantity

    class Meta:
        db_table = 'cart_items'
        unique_together = ('cart', 'product')
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'


class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    contact_phone = models.CharField(max_length=20)

    def generate_order_number(self):
        date_part = timezone.now().strftime('%Y%m%d')
        unique_part = uuid.uuid4().hex[:6].upper()
        return f"ORD-{date_part}-{unique_part}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

    class Meta:
        db_table = 'orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def product_image(self):
        return self.product.main_image if self.product else None

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'


class AuditLog(models.Model):
    ACTION_TYPES = [
        ('INSERT', 'Добавление'),
        ('UPDATE', 'Обновление'),
        ('DELETE', 'Удаление'),
    ]

    action_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    table_name = models.CharField(max_length=50)
    record_id = models.IntegerField(null=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'audit_log'
        ordering = ['-action_time']
        verbose_name = 'Лог изменений'
        verbose_name_plural = 'Логи изменений'
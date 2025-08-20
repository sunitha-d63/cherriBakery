from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from decimal import Decimal

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/', blank=True)
    slug = models.SlugField(unique=True, max_length=150) 
    
    class Meta:
        verbose_name_plural = "Product Categories"
    
    def __str__(self):
        return self.name
    
    @property
    def product_count(self):
        return self.products.count()
    
    def get_absolute_url(self):
        return reverse('category_products', kwargs={'slug': self.slug})

class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    category = models.ForeignKey(
        ProductCategory, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    description = models.TextField(blank=True) 
    detailed_description = models.TextField(blank=True)

    base_price = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Base price per kilogram"
    )
    weight_options = models.CharField(
        max_length=100,
        default="500G,1KG,2KG,3KG,4KG,5KG",
        help_text="Comma-separated weight options"
    )

    nutrition_info = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)
    allergy_info = models.TextField(blank=True)

    image = models.ImageField(upload_to='products/', blank=True)
    
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={
            'category_slug': self.category.slug,
            'product_id': self.id
        })
    
    def image_preview(self):
        return format_html(
            '<img src="{}" width="50" height="50" style="object-fit: cover;" />', 
            self.image.url
        ) if self.image else ""
    image_preview.short_description = 'Image Preview'

    def in_wishlist(self, user):
        """Check if product is in user's wishlist"""
        if not user.is_authenticated:
            return False
        return self.in_wishlists.filter(user=user).exists()
    
    @property
    def formatted_price(self):
        return f"₹{self.base_price} PER KG"
    
    @property
    def weight_list(self):
        return [w.strip() for w in self.weight_options.split(',')]

class UserManager(BaseUserManager):
    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None 
    email = models.EmailField(
        _('email address'),
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address.")]
    )
    first_name = models.CharField(
        _('first name'),
        max_length=30,
        blank=False
    )
    last_name = models.CharField(
        _('last name'),
        max_length=30,
        blank=False
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  
    
    objects = UserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
        super().save(*args, **kwargs)
    
class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='in_wishlists'
    )
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
    
    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.title}"
    

class ContactMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=100)
    message = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"


class Order(models.Model):
    PAYMENT_METHODS = (
        ('upi', 'UPI'),
        ('wallet', 'Digital Wallet'),
        ('credit', 'Credit/Debit Card'),
        ('cod', 'Cash on Delivery'),
    )
    
    ORDER_STATUSES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    customer_name = models.CharField(max_length=100)
    customer_mobile = models.CharField(max_length=15)
    delivery_location = models.CharField(max_length=100)
    delivery_address = models.TextField()
    special_notes = models.TextField(blank=True, null=True)

    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUSES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_completed = models.BooleanField(default=False)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('bakery.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.CharField(max_length=50, blank=True, null=True)  # e.g., "500g", "1kg"
    
    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.title} for Order #{self.order.id}"
    
class Payment(models.Model):
    PAYMENT_STATUSES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment method specific fields
    upi_id = models.CharField(max_length=50, blank=True, null=True)
    wallet_id = models.CharField(max_length=50, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_expiry = models.CharField(max_length=5, blank=True, null=True)  # MM/YY format
    
    def __str__(self):
        return f"Payment for Order #{self.order.id}"
    

from django.db.models import Sum, F

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def subtotal(self):
        return self.items.aggregate(
            subtotal=Sum(F('price') * F('quantity'))
        )['subtotal'] or Decimal('0.00')

    @property
    def tax_amount(self):
        return self.subtotal * Decimal('0.18')  # 18% GST

    @property
    def delivery_charge(self):
        return Decimal('50.00')

    @property
    def total(self):
        return self.subtotal + self.tax_amount + self.delivery_charge


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)  # assumes you have Product model
    weight = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return self.price * self.quantity

    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    weight = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return self.price * self.quantity
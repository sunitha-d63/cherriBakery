from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.html import format_html
from .models import ProductCategory, Product,ContactMessage


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'image_preview')
    readonly_fields = ('product_count', 'image_preview')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _product_count=Count('products')
        )
    
    def product_count(self, obj):
        return obj._product_count  
    product_count.short_description = 'PRODUCT COUNT'
    product_count.admin_order_field = '_product_count'
    
    def image_preview(self, obj):
        try:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover" />', 
                obj.image.url
            ) if obj.image else ""
        except:
            return ""
    image_preview.short_description = 'Image Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category','base_price', 'price_display', 'weight_options_display', 'is_featured', 'image_preview')
    list_filter = ('category', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'detailed_description', 'ingredients','nutrition_info')
    list_editable = ('is_featured',)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('image_preview', 'created_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'category', 'description', 'detailed_description')
        }),
        ('Pricing', {
            'fields': ('base_price', 'weight_options')
        }),
        ('Product Details', {
            'fields': ('nutrition_info', 'ingredients', 'allergy_info')
        }),
        ('Media', {
            'fields': ('image', 'image_preview')
        }),
        ('Status', {
            'fields': ('is_featured', 'created_at')
        }),
    )
    
    def price_display(self, obj):
        if obj.base_price is None:
            return "Not set"
        return f"₹{obj.base_price:.2f} PER KG"  # Ensures 2 decimal places
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'base_price'  # Enable sorting
    
    def weight_options_display(self, obj):
        if not obj.weight_options:
            return "Not set"
    
        weights = [w.strip().upper() for w in obj.weight_options.split(',')]
        bad_weights = [w for w in weights if not w.endswith(('G', 'KG'))]
    
        if bad_weights:
            return format_html(
                '<span style="color:red">Invalid weights: {}</span>',
                ', '.join(bad_weights)
            )
        return ', '.join(weights)
    
    def image_preview(self, obj):
        try:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover" />', 
                obj.image.url
            ) if obj.image else ""
        except:
            return ""
    image_preview.short_description = 'Preview'



@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject', 'user__username')
    list_filter = ('created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')  # Optimize database queries



       
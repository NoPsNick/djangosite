from django.contrib import admin

from .models import Category, Product, Stock, PromotionCode, PromotionCodeUsage

from products.models import Promotion


class StockInline(admin.StackedInline):  # or admin.StackedInline for a more detailed view
    model = Stock
    fields = ['units', 'units_sold', 'units_hold']
    readonly_fields = ['units_sold', 'units_hold']  # Make fields read-only as needed
    extra = 0  # No extra blank forms by default
    can_delete = False  # Disable deletion to ensure each product has a single stock entry
    max_num = 1

    def has_add_permission(self, request, obj=None):
        # Prevent adding stock manually; it should only be created when a product is created
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_available', 'is_role', 'created', 'modified']
    list_filter = ['is_available', 'category', 'is_role']
    search_fields = ['name', 'slug', 'description']
    autocomplete_fields = ['category', 'role_type']
    readonly_fields = ['created', 'modified']
    ordering = ['-modified']
    inlines = [StockInline]  # Add the Stock inline to the Product admin view

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category', 'role_type')

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Update product availability based on stock units after saving
        product = form.instance
        if product.stock:
            product.is_available = product.stock.units > 0
            product.save(update_fields=['is_available'])


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created', 'modified']
    search_fields = ['name', 'slug']
    ordering = ['name']
    readonly_fields = ['created', 'modified']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'units', 'units_sold', 'units_hold', 'created', 'modified']
    search_fields = ['product__name']
    ordering = ['-created']
    autocomplete_fields = ['product']
    readonly_fields = ['created', 'modified']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product')


class PromotionInline(admin.TabularInline):
    model = Promotion
    fields = ['name', 'status', 'starts_at', 'expires_at', 'changed_price', 'original_price']
    readonly_fields = ['original_price']
    extra = 0
    can_delete = False


class PromotionCodeUsageInline(admin.TabularInline):
    model = PromotionCodeUsage
    fields = ['user', 'user_usage_count', 'created', 'modified']
    readonly_fields = ['created', 'modified']
    extra = 0
    can_delete = False


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'status', 'starts_at', 'expires_at', 'changed_price', 'original_price',
                    'created']
    list_filter = ['status', 'starts_at', 'expires_at']
    search_fields = ['name', 'product__name']
    autocomplete_fields = ['product']
    ordering = ['-created']
    readonly_fields = ['created', 'modified']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product')


@admin.register(PromotionCode)
class PromotionCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status', 'product', 'category', 'role', 'usage_count', 'usage_limit', 'start_at',
                    'expires_at']
    list_filter = ['status', 'start_at', 'expires_at', 'category', 'product', 'role']
    search_fields = ['name', 'code', 'user__username', 'product__name', 'category__name', 'role__name']
    autocomplete_fields = ['user', 'product', 'category', 'role']
    ordering = ['-created']
    readonly_fields = ['created', 'modified']
    inlines = [PromotionCodeUsageInline]  # Inline for tracking promotion code usage by user

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'product', 'category', 'role')


@admin.register(PromotionCodeUsage)
class PromotionCodeUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'promotion_code', 'user_usage_count', 'created']
    search_fields = ['user__username', 'promotion_code__code']
    ordering = ['-created']
    autocomplete_fields = ['user', 'promotion_code']
    readonly_fields = ['created', 'modified']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'promotion_code')

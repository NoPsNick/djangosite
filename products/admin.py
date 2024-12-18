from django.contrib import admin
from django.db.models import Q

from .models import Category, Product, Stock, PromotionCode, PromotionCodeUsage

from products.models import Promotion


class StockInline(admin.StackedInline):  # or admin.StackedInline for a more detailed view
    model = Stock
    fields = ['units', 'units_sold', 'units_hold']
    readonly_fields = ['units_sold', 'units_hold']  # Make fields read-only as needed
    extra = 1
    can_delete = False  # Disable deletion to ensure each product has a single stock entry
    max_num = 1


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
        return queryset.select_related('category', 'role_type').prefetch_related('stock')

    def get_search_results(self, request, queryset, search_term):
        """
        Optimize search results for the admin's autocomplete fields and other search functionalities.
        """
        queryset = queryset.select_related('category', 'role_type')  # Optimize foreign keys
        queryset = queryset.prefetch_related('stock')  # Optimize related data
        if search_term:
            # Apply search filters on the fields defined in `search_fields`
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(slug__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        return super().get_search_results(request, queryset, search_term)


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
    list_display = ['code', 'name', 'status', 'product', 'role', 'usage_count', 'usage_limit', 'start_at',
                    'expires_at']
    list_filter = ['status', 'start_at', 'expires_at', 'product', 'role']
    search_fields = ['name', 'code', 'user__username', 'product__name', 'role__name']
    autocomplete_fields = ['user', 'product', 'role']
    ordering = ['-created']
    readonly_fields = ['created', 'modified']
    inlines = [PromotionCodeUsageInline]  # Inline for tracking promotion code usage by user

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'product', 'role')


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

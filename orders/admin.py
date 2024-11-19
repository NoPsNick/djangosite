from django.contrib import admin
from django.db.models import Prefetch

from products.models import Product
from .models import Item, Order


class ItemInline(admin.TabularInline):
    model = Item
    extra = 0
    max_num = 0
    autocomplete_fields  = ['product']
    readonly_fields = ['product', 'quantity']
    can_delete = False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('order', 'product').order_by('-id')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'products_product':
            # Provide an optimized queryset for products
            kwargs['queryset'] = Product.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    ordering = ['product__name']
    list_display = ['order', 'product', 'quantity', 'get_total_price']
    search_fields = ['order__id', 'product__name']
    autocomplete_fields  = ['order', 'product']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('order', 'product').order_by('-id')

    def get_total_price(self, obj):
        return obj.get_total_price()

    get_total_price.short_description = 'Total Price'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields  = ['customer']
    list_display = ['id', 'customer', 'status', 'is_paid', 'modified']
    list_filter = ['status', 'is_paid', 'modified']
    search_fields = ['customer__username', 'id']
    readonly_fields = ['status', 'created', 'modified']
    inlines = [ItemInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('customer')

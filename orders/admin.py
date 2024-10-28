from django.contrib import admin
from django.db.models import Prefetch
from .forms import ItemForm, OrderForm
from .models import Item, Order


class ItemInline(admin.TabularInline):
    model = Item
    extra = 1
    form = ItemForm
    autocomplete_fields  = ['product']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product').order_by('-id')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    ordering = ['product__name']
    list_display = ['order', 'product', 'quantity', 'get_total_price']
    search_fields = ['order__id', 'product__name']
    form = ItemForm
    autocomplete_fields  = ['order', 'product']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('order', 'product').order_by('-id')

    def get_total_price(self, obj):
        return obj.get_total_price()

    get_total_price.short_description = 'Total Price'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderForm
    autocomplete_fields  = ['customer']
    list_display = ['id', 'customer', 'status', 'is_paid', 'modified', 'get_total_amount']
    list_filter = ['status', 'is_paid', 'modified']
    search_fields = ['customer__username', 'id']
    readonly_fields = ['status', 'created', 'modified']
    inlines = [ItemInline]
    # actions = ['mark_as_paid']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Use select_related for customer (ForeignKey) and prefetch_related for items (Reverse FK)
        return queryset.select_related('customer').prefetch_related(
            Prefetch('items', queryset=Item.objects.select_related('product'))
        ).order_by('-id')

    def get_total_amount(self, obj):
        return obj.get_total_amount()

    get_total_amount.short_description = 'Total Amount'

    # def mark_as_paid(self, request, queryset):
    #     updated_count = queryset.update(is_paid=True)
    #     self.message_user(request, f'{updated_count} orders marked as paid.')
    #
    # mark_as_paid.short_description = 'Mark selected orders as paid'

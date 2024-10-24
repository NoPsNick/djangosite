from django.contrib import admin

from .forms import ItemForm, OrderForm
from .models import Item, Order


class ItemInline(admin.TabularInline):
    model = Item
    extra = 1
    form = ItemForm
    raw_id_fields = ['product']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    ordering = []
    form = ItemForm

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderForm
    raw_id_fields = ['customer']
    inlines = [ItemInline]

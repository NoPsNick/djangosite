from django.contrib import admin

from .models import Category, Product, Stock

from products.models import Promotion


class EstoqueInline(admin.TabularInline):
    model = Stock
    max_num = 1
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created", "modified"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "category",
        "price",
        "is_available",
        "created",
        "modified",
    ]
    list_filter = ["is_available", "created", "modified"]
    list_editable = ["price", "is_available"]
    inlines = [EstoqueInline]


@admin.register(Stock)
class EstoqueAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "units",
        "units_sold",
        "created",
        "modified",
    ]
    list_filter = ["units", "units_sold", "created", "modified"]


@admin.register(Promotion)
class PromotionsAdmin(admin.ModelAdmin):
    pass
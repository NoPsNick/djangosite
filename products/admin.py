from django.contrib import admin

from .models import Category, Product, Stock

from products.models import Promotion


class StockInline(admin.TabularInline):
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
    inlines = [StockInline]

    def save_model(self, request, obj, form, change):
        # Aqui você pode garantir que o objeto seja criado primeiro
        if not obj.pk:
            # Se o objeto ainda não existir (caso de criação), salve-o primeiro
            obj.save()
        super().save_model(request, obj, form, change)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "units",
        "units_sold",
        "created",
        "modified",
    ]
    list_filter = ["units", "units_sold", "created", "modified"]

    def save_model(self, request, obj, form, change):
        # Aqui você pode garantir que o objeto seja criado primeiro
        if not obj.pk:
            # Se o objeto ainda não existir (caso de criação), salve-o primeiro
            obj.save()
        super().save_model(request, obj, form, change)


@admin.register(Promotion)
class PromotionsAdmin(admin.ModelAdmin):
    pass

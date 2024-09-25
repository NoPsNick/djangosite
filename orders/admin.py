from django.contrib import admin

from orders.models import Item, Order


# Register your models here.
@admin.register(Item)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass
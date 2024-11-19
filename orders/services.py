from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.cache import cache

from products.services import get_stock_from_cache
from .models import Order, Item


def create_order(user, items_data, products):
    with transaction.atomic():
        # Create the order
        order = Order.objects.create(customer=user, status=Order.Waiting_payment)

        # Map slug to product for quick lookup
        product_map = {product.slug: product for product in products}

        items_to_create = []
        for item_data in items_data:
            product = product_map.get(item_data['slug'])
            if not product:
                raise ValidationError(f"O produto {item_data['slug']} não foi encontrado.")

            product.check_promotions()

            quantity = item_data['quantity']

            # Check stock from cache or product instance
            stock = get_stock_from_cache(item_data['slug'])
            if stock and getattr(stock, 'units', 0) < quantity:
                raise ValidationError(f"O produto {product.name} está sem estoque no momento.")

            items_to_create.append(Item(order=order, product=product, quantity=quantity))

        # Bulk create all items
        Item.objects.bulk_create(items_to_create)

    cache_key = orders_cache_key_builder(user.id)
    cache.delete(cache_key)
    return order

def orders_cache_key_builder(user_id):
    return f'orders_{user_id}_dict'

from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.cache import cache

from products.models import Product
from products.services import get_stock_from_cache
from .models import Order, Item


def create_order(user, items_data):
    """
    Create an order with items, checking stock.
    Args:
        user: The user creating the order.
        items_data: List of items to be added to the order (slug, quantity).
        :return: The order
    """
    with transaction.atomic():
        # Create the order
        order = Order.objects.create(customer=user, status=Order.Waiting_payment)

        # Gather slugs for batch querying
        slugs = [item['slug'] for item in items_data]

        # Retrieve all products and their stock in one query
        products = Product.objects.filter(slug__in=slugs).select_related('stock', 'role_type')

        # Map slug to product for quick lookup
        product_map = {product.slug: product for product in products}

        items_to_create = []
        for item_data in items_data:
            product = product_map.get(item_data['slug'])
            if not product:
                raise ValidationError(f"O produto {item_data['slug']} não foi encontrado.")

            quantity = item_data['quantity']

            # Check stock from cache or product instance
            stock = get_stock_from_cache(item_data['slug']) or getattr(product, 'stock', None)
            if stock and stock.get('units') < quantity:
                raise ValidationError(f"O produto {product.name} está sem estoque no momento.")

            items_to_create.append(Item(order=order, product=product, quantity=quantity))

        # Bulk create all items
        Item.objects.bulk_create(items_to_create)

        # Save order and clear cache
        order.save()
        cache_key = orders_cache_key_builder(user.id)
        cache.delete(cache_key)

    return order

def orders_cache_key_builder(user_id):
    return f'orders_{user_id}_dict'

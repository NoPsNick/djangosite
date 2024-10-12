from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
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

        # Iterate over items to add to order
        for item_data in items_data:
            product = get_object_or_404(Product, slug=item_data['slug'])

            if not product:
                raise ValidationError(f"O produto {item_data['slug']} não foi encontrado.")

            quantity = item_data['quantity']

            # Check if the product has stock
            stock = get_stock_from_cache(item_data['slug']) # Get the stock from cache if exists
            if stock:
                if stock['units'] <= quantity:
                    raise ValidationError(f"O produto {product.name}, está sem estoque no momento.")

            Item.objects.create(
                order=order,
                product=product,
                quantity=quantity
            )
        order.save()
        cache_key = f'orders_{user}_list'
        cache.delete(cache_key)  # Clear the user's order list cache

        # Optionally, you can also clear any other cached data related to the order
        cache_key_single_order = f'order_{user}_{order.id}'
        cache.delete(cache_key_single_order)  # Clear cache for individual order

    return order

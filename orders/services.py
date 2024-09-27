from django.db import transaction
from django.core.exceptions import ValidationError

from products.services import get_product_from_cache, get_stock_from_cache
from .models import Order, Item


def create_order(user, items_data):
    """
    Create an order with items, checking stock.
    Args:
        user: The user creating the order.
        items_data: List of items to be added to the order (slug, quantity).
    """

    with transaction.atomic():
        # Create the order
        order = Order.objects.create(user=user)

        # Iterate over items to add to order
        for item_data in items_data:
            product = get_product_from_cache(slug=item_data['slug'])

            if not product:
                raise ValidationError(f"The product {item_data['slug']} does not exist.")

            quantity = item_data['quantity']

            # Check if the product has stock
            stock = get_stock_from_cache(item_data['slug']) # Get the stock from cache if exists
            if stock:
                if stock['units'] <= quantity:
                    raise ValidationError(f"Not enough stock for product {product['name']}.")

            Item.objects.create(
                order=order,
                product=product,
                quantity=quantity
            )

        order.status = Order.Waiting_payment
        order.save()

    return order

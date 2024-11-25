from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.cache import cache

from products.services import get_stock_from_cache, get_product_from_cache
from .models import Order, Item


def create_order(user, items_data):
    with transaction.atomic():
        # Create and save the order (not inserted into the DB until save is called)
        order = Order.objects.create(customer=user, status=Order.Waiting_payment)

        items_to_create = []
        for item_data in items_data:
            product = get_product_from_cache(item_data['slug'])
            quantity = item_data['quantity']

            # Check stock from cache or product instance
            stock = get_stock_from_cache(item_data['slug'])
            if stock and getattr(stock, 'units', 0) < quantity:
                raise ValidationError(f"O produto {product['name']} está sem estoque no momento.")

            # Associate the saved order with the items
            items_to_create.append(
                Item(order=order,
                     product_id=product['id'],
                     name=product['name'],
                     price=product['price'],
                     slug=product['slug'],
                     quantity=quantity)
            )
        Item.objects.bulk_create(items_to_create)
        order.save()

    return order

def orders_cache_key_builder(user_id):
    return f'orders_{user_id}_dict'

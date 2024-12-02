from django.db import transaction
from django.core.exceptions import ValidationError

from products.services import get_stock_from_cache, get_product_from_cache
from .models import Order, Item

import logging

logger = logging.getLogger('celery')


def create_order(user, items_data) -> Order | ValidationError | Exception:
    try:
        with transaction.atomic():
            # Create and save the order
            order = Order.objects.create(customer=user, status=Order.Waiting_payment)
            items_to_create = []

            for item_data in items_data:
                product = get_product_from_cache(item_data['slug'])
                quantity = item_data['quantity']
                stock = get_stock_from_cache(item_data['slug'])

                # Check stock from cache or product instance
                if stock and getattr(stock, 'units', 0) < quantity:
                    raise ValidationError(f"O produto {product['name']} está sem estoque no momento.")

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
    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error while creating order for user {user.id}: {e}")
        raise


def orders_cache_key_builder(user_id):
    return f'orders_{user_id}_dict'

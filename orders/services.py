from django.db import transaction
from django.core.exceptions import ValidationError

from products.models import Product, PromotionCode
from .models import Order, Item


def create_order(user, items_data, promo_code=None):
    """
    Create an order with items, checking stock and applying promotions.
    Args:
        user: The user creating the order.
        items_data: List of items to be added to the order (slug, quantity).
        promo_code: Optional promotion code to apply.
    """
    with transaction.atomic():
        # Create the order
        order = Order.objects.create(user=user)

        # Iterate over items to add to order
        for item_data in items_data:
            product = Product.objects.get(slug=item_data['slug'])
            quantity = item_data['quantity']

            # Check if the product has stock
            stock = getattr(product, 'estoque', None)  # Get the stock object if exists
            if stock:
                if not stock.can_sell(quantity):
                    raise ValidationError(f"Not enough stock for product {product.name}.")
                # Deduct stock after validation
                stock.sell(quantity)

            # Apply the promotion code if provided
            if promo_code:
                promotion_code: PromotionCode = PromotionCode.objects.get(code=promo_code)
                promotion_code.is_valid(user=user)  # Validate the promotion code
                # Increment the usage of the promotion code
                promotion_code.increment_usage(user=user)

                Item.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    promotion_code=promotion_code,
                )
            # Add the item to the order without a promotion code
            else:
                Item.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity
                )

        order.status = Order.Aguardando
        order.save()

    return order

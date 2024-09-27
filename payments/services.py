from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError

from payments.models import Payment, PaymentPromotionCode
from products.models import Product, Stock, PromotionCode
from orders.models import Order


def create_payment(user, order: Order, promo_codes: list=None):
    """
    Create a payment based in the request, order and if there's any promotion code, discount the products prices if
    they are valid.
    :param user: The user creating the payment
    :param order: Order object
    :param promo_codes: a list of promotion codes
    :return: the created payment object
    """

    total_price = sum(item.get_total_price() for item in order.items.all())
    valid_promo_codes = []

    if order.is_paid:
        raise ValidationError("Order is already paid")
    if order.status == order.Cancelled:
        raise ValidationError("Order is already cancelled")

    with transaction.atomic():
        payment = Payment.objects.create(customer=user, order=order, price=total_price)

        # Apply promo codes if provided
        if promo_codes:
            for code in promo_codes:
                promo_code = get_object_or_404(PromotionCode, code=code)

                try:
                    # Validate the promo code
                    if not promo_code.is_valid(user=user):
                        raise ValidationError(f"Promo code {promo_code.code} is not valid.")

                    # Apply discount
                    for item in order.items.all():
                        product = item.product
                        try:
                            product.check_not_updated_promotions()
                        except ValidationError as e:
                            order.status = order.Cancelled
                            order.save()
                            raise ValidationError(f"The {product.name} has an error, please create another order. "
                                                  f"Reason: {e}")
                        category = product.category

                        try:
                            discounted_price = promo_code.apply_discount(product, category=category)
                            total_price = total_price - (product.price - discounted_price) * item.quantity
                        except ValidationError as e:
                            raise ValidationError(f"Promo code {promo_code.code} cannot be applied: {str(e)}")

                    # Add promo code to the list of valid codes
                    valid_promo_codes.append(promo_code)

                except ValidationError as e:
                    # Handle invalid promo code
                    raise ValidationError(f"Failed to apply promo code {code}: {str(e)}")

            # Update payment price with the discounted total price
            payment.price = total_price
            payment.save()

            # Create entries in the intermediate table for valid promo codes
            for promo_code in valid_promo_codes:
                PaymentPromotionCode.objects.create(payment=payment, promotion_code=promo_code)

        # Handle stock and finalize payment creation
        for item in order.items.all():
            product: Product = get_object_or_404(Product, pk=item.product.pk)
            stock: Stock = product.estoque

            if stock and not stock.can_sell():
                raise ValidationError(f"Not enough stock for product {product.name}")
            stock.sell(quantity=item.quantity)

        # Increment usage for the valid promo codes
        for promo_code in valid_promo_codes:
            promo_code.increment_usage(user=user)

    return payment

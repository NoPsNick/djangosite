from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import F, Sum

from payments.models import Payment, PaymentPromotionCode, PaymentStatus, PaymentMethod
from products.models import PromotionCode
from orders.models import Order

User = get_user_model()


def create_payment(user: User, order: Order, payment_method: PaymentMethod, promo_codes: list = None):
    """
    Create a payment based on the user, order, and apply any valid promotion codes, discounting product prices if
    applicable.
    :param payment_method: Payment method to use
    :param user: The user creating the payment
    :param order: Order object
    :param promo_codes: a list of promotion codes
    :return: the created payment object
    """

    # Check if the order is already paid or cancelled
    if order.is_paid:
        raise ValidationError("Order is already paid")
    if order.status == order.Cancelled:
        raise ValidationError("Order is cancelled")

    # Prefetch related order items and their products
    order_items = order.items.select_related('product').all()

    # Calculate the initial total price (without discount)
    total_price = order_items.aggregate(total_price=Sum(F('product__price') * F('quantity')))['total_price']

    valid_promo_codes = []
    final_total_price = 0  # Initialize the final total price

    with transaction.atomic():
        payment = Payment.objects.create(customer=user, order=order, amount=total_price, payment_method=payment_method)

        # Apply promotion codes if provided
        if promo_codes:
            for code in promo_codes:
                promo_code = get_object_or_404(PromotionCode, code=code)

                try:
                    # Validate the promo code (raises ValidationError if invalid)
                    promo_code.is_valid(user=user)

                    # Apply discount to each item in the order
                    for item in order_items:
                        product = item.product

                        # Check if product promotions are up to date
                        try:
                            product.check_not_updated_promotions()
                        except ValidationError as e:
                            order.status = order.Cancelled
                            order.save()
                            raise ValidationError(f"Error with product {product.name}, please create another order. "
                                                  f"Reason: {e}")

                        # Apply discount based on promo code
                        category = product.category
                        try:
                            # Get the discounted price from the promotion
                            discounted_price = promo_code.apply_discount(product, category=category)

                            # Update the final total price with the discounted price for this item
                            final_total_price += discounted_price * item.quantity
                        except ValidationError as e:
                            raise ValidationError(f"Promo code {promo_code.code} cannot be applied: {str(e)}")

                    # Add valid promo code to the list
                    valid_promo_codes.append(promo_code)

                except ValidationError as e:
                    raise ValidationError(f"Failed to apply promo code {code}: {str(e)}")

            # Update payment with the discounted price (final total after applying discounts)
            payment.amount = final_total_price
            payment.save()

            # Create payment-promo code link
            PaymentPromotionCode.objects.bulk_create([
                PaymentPromotionCode(payment=payment, promotion_code=promo_code)
                for promo_code in valid_promo_codes
            ])
        else:
            # No promo codes were applied, use the initial total price
            final_total_price = total_price
            payment.amount = final_total_price
            payment.save()

        # Handle stock and finalize payment creation
        for item in order_items:
            product = item.product
            stock = product.stock

            if stock and not stock.can_sell(item.quantity):
                raise ValidationError(f"Not enough stock for product {product.name}")

            # Reduce stock quantity in an atomic transaction
            stock.sell(quantity=item.quantity)

        # Increment usage count for the valid promo codes
        for promo_code in valid_promo_codes:
            promo_code.increment_usage(user=user)

        payment.order.status = order.Waiting_payment
        payment.order.save(update_fields=['status'])
    return payment


@transaction.atomic
def refund_payment(payment: Payment):
    payment.status = PaymentStatus.REFUNDED
    payment.save(update_fields=['status'])

    payment.order.status = Order.Cancelled
    payment.order.is_paid = False
    payment.order.save(update_fields=['status', 'is_paid'])

    order_items = payment.order.items.select_related('product').all()

    for item in order_items:
        product = item.product
        stock = product.stock

        if stock:
            stock.restore(quantity=item.quantity)

    payments_promo_codes = payment.used_coupons.all()

    for payment_code in payments_promo_codes:
        promo_code = payment_code.promotion_code
        promo_code.restore_usage(user=payment.customer)
        payment_code.delete()


@transaction.atomic
def complete_payment(payment: Payment):
    payment.status = PaymentStatus.COMPLETED
    payment.save(update_fields=['status'])

    payment.order.status = Order.Finalized
    payment.order.is_paid = True
    payment.order.save(update_fields=['status', 'is_paid'])

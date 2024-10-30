import logging
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from django.core.cache import cache

from .customexceptions import PaymentProcessingError
from .models import Payment, PaymentPromotionCode, PaymentStatus, PaymentMethod
from products.models import PromotionCode
from orders.models import Order
from users.models import Role

User = get_user_model()
logger = logging.getLogger('celery')


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
        raise ValidationError("Pedido já foi pago.")
    if order.status == order.Cancelled:
        raise ValidationError("Este pedido foi cancelado.")

    order_items = order.items.select_related('product').all()
    total_price = order_items.aggregate(total_price=Sum(F('product__price') * F('quantity')))['total_price']
    valid_promo_codes = []
    final_total_price = total_price  # Initialize the final total price to the initial total price

    try:
        with transaction.atomic():
            payment = Payment.objects.create(
                customer=user,
                order=order,
                amount=total_price,
                payment_method=payment_method
            )

            # Apply promotion codes if provided
            if promo_codes:
                promo_code_objs = PromotionCode.objects.filter(code__in=promo_codes)
                for promo_code in promo_code_objs:
                    try:
                        promo_code.is_valid(user=user)
                        for item in order_items:
                            product = item.product
                            try:
                                product.check_not_updated_promotions()
                            except ValidationError as e:
                                order.status = order.Cancelled
                                order.save()
                                raise ValidationError(
                                    f"Error with product {product.name}, please create another order. "
                                    f"Reason: {e}")

                            category = product.category
                            discounted_price = promo_code.apply_discount(product, category=category)
                            final_total_price += discounted_price * item.quantity

                        valid_promo_codes.append(promo_code)

                    except ValidationError as e:
                        raise ValidationError(f"Failed to apply promo code {promo_code.code}: {str(e)}")

                payment.amount = final_total_price
                payment.save(default_service=True)

                PaymentPromotionCode.objects.bulk_create([
                    PaymentPromotionCode(payment=payment, promotion_code=promo_code)
                    for promo_code in valid_promo_codes
                ])

            # Handle stock
            for item in order_items:
                stock = getattr(item.product, 'stock', None)
                if stock and not stock.can_sell(item.quantity):
                    raise ValidationError(f"Not enough stock for product {product.name}")
                stock.sell(quantity=item.quantity)

            # Increment promo code usage
            for promo_code in valid_promo_codes:
                promo_code.increment_usage(user=user)

            payment.order.status = order.Waiting_payment
            payment.order.save(update_fields=['status'])

    except Exception as e:
        logger.error(f"Error trying to create the payment: {e}.")
        raise ValidationError("An error occurred while creating the payment.")

    cache.delete(payments_cache_key_builder(user.id))
    return payment


def process_payment_status(payment: Payment, order_items=None):
    from orders.models import Order

    # Determine new status and proceed only if conditions are met
    if payment.status == PaymentStatus.COMPLETED:
        new_status = PaymentStatus.REFUNDED
    elif payment.status == PaymentStatus.PENDING:
        new_status = PaymentStatus.CANCELLED
    else:
        # Exit if payment status doesn't match refundable or cancelable status
        return

    try:
        with transaction.atomic():
            # Update payment status
            payment.status = new_status
            payment.save(update_fields=['status'], default_service=True)

            # Refund or restore items in order
            order_items = order_items or payment.order.items.select_related('product').all()
            for item in order_items:
                stock = getattr(item.product, 'stock', None)
                if stock:
                    stock.restore(
                        quantity=item.quantity) if payment.order.status != Order.Waiting_payment else stock.restore_hold(
                        quantity=item.quantity)

            # Update order status to 'cancelled' and mark as unpaid
            payment.order.status = Order.Cancelled
            payment.order.is_paid = False
            payment.order.save(update_fields=['status', 'is_paid'])

            # Handle coupon restoration
            for payment_code in payment.used_coupons.all():
                payment_code.promotion_code.restore_usage(user=payment.customer)
                payment_code.delete()

            # Clear related cache
            cache.delete(payments_cache_key_builder(payment.customer.id))

    except Exception as e:
        # Log the error or handle it as needed
        logger.error(f"Error processing payment status for payment ID {payment.id}: {e}. "
                     f"Payment status: {payment.status}. "
                     f"Trying to change to the payment new status: {new_status}")
        raise PaymentProcessingError("An error occurred while processing the payment.")


def finish_successful_payment(payment: Payment):
    from users.services import RolePermissionService
    if payment.status == PaymentStatus.PENDING:
        try:
            with transaction.atomic():
                user = payment.customer
                order_items = payment.order.items.select_related('product', 'product__stock').all()

                # Process each item in the order
                for item in order_items:
                    product = item.product

                    # Assign roles if the product is a role type
                    if product.is_role:
                        if not product.is_role_product():
                            process_payment_status(payment, order_items=order_items)
                            raise ValidationError('This product is not a role, contact an administrator.')

                        # Create and save the new role
                        new_role = Role(user=user, role_type=product.role_type)
                        new_role.save()
                        RolePermissionService().update_user_role(user=user, new_role=new_role)

                    # Update stock for successful sale
                    stock = getattr(product, 'stock', None)
                    if stock:
                        stock.successful_sell(quantity=item.quantity)

                # Update payment status to completed and mark order as in transit
                payment.status = PaymentStatus.COMPLETED
                payment.save(update_fields=['status'], default_service=True)

                payment.order.status = Order.Way
                payment.order.is_paid = True
                payment.order.save(update_fields=['status', 'is_paid'])

                # Clear related cache
                cache.delete(payments_cache_key_builder(payment.customer.id))
        except Exception as e:
            # Log the error or handle it as needed
            logger.error(f"Error processing payment status for payment ID {payment.id}: {e}. ")
            raise PaymentProcessingError("An error occurred while processing the payment.")


def payments_cache_key_builder(user_id):
    return f'payments_{user_id}_dict'

import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from django.core.cache import cache
from decimal import Decimal
from django.utils import timezone

from .models import Payment, PaymentPromotionCode, PaymentStatus, PaymentMethod
from products.models import PromotionCode
from orders.models import Order
from users.models import Role

User = get_user_model()
logger = logging.getLogger('celery')


def create_payment(user: User, order: Order, payment_type, promo_codes: list = None):
    """
    Create a payment based on the user, order, and apply any valid promotion codes, discounting product prices if
    applicable.
    :param payment_type: Payment method type to use
    :param user: The user creating the payment
    :param order: Order object
    :param promo_codes: a list of promotion codes
    :return: the created payment object
    """
    try:
        # Check if the order is already paid or cancelled
        if order.is_paid:
            raise ValidationError("Pedido já foi pago.")
        if order.status == order.Cancelled:
            raise ValidationError("Este pedido foi cancelado.")

        order_items = order.items.select_related('product', 'product__stock').all()
        total_price = order_items.aggregate(total_price=Sum(F('product__price') * F('quantity')))['total_price']
        valid_promo_codes = []
        final_total_price = total_price  # Initialize the final total price to the initial total price

        with transaction.atomic():
            payment_method = PaymentMethod.objects.create(name='', payment_type=payment_type)
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

                            category = product.category
                            discounted_price = promo_code.apply_discount(product, category=category)
                            final_total_price -= discounted_price * item.quantity

                        valid_promo_codes.append(promo_code)

                    except ValidationError as e:
                        raise ValidationError(f"Failed to apply promo code {promo_code.code}: {str(e)}")


                PaymentPromotionCode.objects.bulk_create([
                    PaymentPromotionCode(payment=payment, promotion_code=promo_code)
                    for promo_code in valid_promo_codes
                ])

            # Handle stock
            for item in order_items:
                stock = getattr(item.product, 'stock', None)
                product = item.product
                try:
                    product.check_not_updated_promotions()
                except ValidationError as e:
                    order.status = order.Cancelled
                    order.save()

                    payment.status = PaymentStatus.FAILED
                    payment.amount = final_total_price
                    payment.save(default_service=True)
                    raise ValidationError(
                        f"Error with product {product.name}, please create another order. "
                        f"Reason: {e}")
                if stock:
                    if not stock.can_sell(item.quantity):
                        raise ValidationError(f"Não temos estoque suficiente para o produto: {product.name}")
                    stock.sell(quantity=item.quantity)

            # Increment promo code usage
            for promo_code in valid_promo_codes:
                promo_code.increment_usage(user=user)

            user_balance_check = payment.customer.pay_with_balance(amount=final_total_price)
            if user_balance_check[0]:
                payment.amount = final_total_price
                finish_successful_payment(payment=payment)
            elif not user_balance_check[0]:
                payment.amount = Decimal(final_total_price - user_balance_check[1])
                payment.save(default_service=True)
                payment.order.status = order.Waiting_payment
                payment.order.save(update_fields=['status'])

        cache.delete(payments_cache_key_builder(user.id))
        return payment
    except Exception as e:
        raise ValidationError(str(e))


def process_payment_status(payment: Payment, items=None):
    from orders.models import Order

    # Determine new status and proceed only if conditions are met
    if payment.status == PaymentStatus.COMPLETED:
        new_status = PaymentStatus.REFUNDED
    elif payment.status == PaymentStatus.PENDING:
        new_status = PaymentStatus.CANCELLED
    else:
        # Raise an exception if payment new_status doesn't match refundable or cancelable status
        raise ValidationError(f"Wrong payment status: {payment.status}. It's only possible to update "
                              f"{PaymentStatus.PENDING} -> {PaymentStatus.CANCELLED} or {PaymentStatus.COMPLETED} -> "
                              f"{PaymentStatus.REFUNDED}.")

    try:
        with transaction.atomic():
            # Refund or restore items in order
            order_items = items or payment.order.items.select_related('product', 'product__stock').all()
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

            # Update payment status
            payment.status = new_status
            payment.save(update_fields=['status'], default_service=True)

            # Clear related cache
            cache.delete(payments_cache_key_builder(payment.customer.id))

    except Exception as e:
        # Log the error or handle it as needed
        logger.error(f"Error processing payment status for payment ID {payment.id}: {e}. "
                     f"Payment status: {payment.status}. "
                     f"Trying to change to the payment new status: {new_status}")
        raise ValidationError("An error occurred while processing the payment refund.")

    # If no exceptions and the payment was refunded, give to the user his balance.
    if new_status == PaymentStatus.REFUNDED:
        payment.customer.refund_to_balance(payment.amount)


def finish_successful_payment(payment: Payment):
    if payment.status == PaymentStatus.PENDING:
        try:
            with transaction.atomic():
                user = payment.customer
                order_items = payment.order.items.select_related('product', 'product__stock', "product__role_type").all()

                # Process each item in the order
                for item in order_items:
                    product = item.product

                    # Check if the product is a role type
                    if product.is_role:
                        if not product.is_role_product():
                            process_payment_status(payment, items=order_items)
                            raise ValidationError('This product is not a role, contact an administrator.')

                        # Check for an existing active or expired role of the same type
                        existing_role = Role.objects.filter(user=user, role_type=product.role_type).first()
                        if existing_role:
                            # Extend the expiration if a role exists
                            if existing_role.is_expired():
                                existing_role.expires_at = timezone.now() + product.role_type.effective_days
                            else:
                                existing_role.expires_at += product.role_type.effective_days
                            existing_role.save(update_fields=['expires_at'])
                        else:
                            # Create a new role if none exists
                            new_role = Role(user=user, role_type=product.role_type)
                            new_role.save()

                    # Update stock for successful sale
                    stock = getattr(product, 'stock', None)
                    if stock:
                        stock.successful_sell(quantity=item.quantity)

                # Update payment status to completed and mark order as finalized
                payment.status = PaymentStatus.COMPLETED
                payment.save(update_fields=['status'], default_service=True)

                payment.order.status = Order.Finalized
                payment.order.is_paid = True
                payment.order.save(update_fields=['status', 'is_paid'])

                # Clear related cache
                cache.delete(payments_cache_key_builder(payment.customer.id))
        except Exception as e:
            # Log the error or handle it as needed
            logger.error(f"Error processing payment status for payment ID {payment.id}: {e}. ")
            raise ValidationError("An error occurred while processing the payment.")


def payments_cache_key_builder(user_id):
    return f'payments_{user_id}_dict'

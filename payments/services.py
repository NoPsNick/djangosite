import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import F, Sum, Prefetch
from django.core.cache import cache
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from .models import Payment, PaymentPromotionCode, PaymentStatus, PaymentMethod
from products.models import PromotionCode
from orders.models import Order
from users.models import Role, UserHistory

User = get_user_model()
logger = logging.getLogger('celery')


class PaymentService:
    """
    Handles payment creation and processing, including applying promotions, updating stock, and managing payment status.
    """

    def __init__(self, payment: Payment = None):
        self.payment = payment
        self.user = None
        self.order = None
        self.payment_type = None
        self.promo_codes = None
        self.total_price = None
        self.order_items = None
        self.valid_promo_codes = []

    def create_payment(self, user: User, order: Order, payment_type, promo_codes: list = None):
        """
        Initializes the payment creation process.

        :param user: User initiating the payment.
        :param order: Order object associated with the payment.
        :param payment_type: Payment method type.
        :param promo_codes: List of promotion codes (optional).
        :return: The created Payment object.
        """
        self.user = user
        self.order = order
        self.payment_type = payment_type
        self.promo_codes = promo_codes
        self.total_price, self.order_items = self._get_order_info()
        self.valid_promo_codes = []

        self._validate_order_status()

        try:
            with transaction.atomic():
                self.payment = self._create_payment()
                final_total_price = self._process_promotions(self.payment)

                self._update_stock()
                self._finalize_payment(self.payment, final_total_price)

                return self.payment
        except Exception as e:
            self._rollback_payment(e)
            raise ValidationError("Erro ao criar o pagamento.")
        finally:
            clear_payment_cache(self.user)

    def process_payment_status(self, new_status=None, items=None):
        """
        Updates the status of an existing payment and handles related order and stock adjustments.

        :param new_status: New status to set for the payment.
        :param items: Order items to process (optional, defaults to all items in the order).
        """
        if not self.payment:
            raise ValueError("Payment instance is required for processing status.")
        self._process_payment_status(items=items, new_status=new_status)

    def finish_successful_payment(self, order=None, user=None, order_items=None):
        """
        Completes the payment process, handling role products and finalizing the order.
        """
        if not self.payment:
            raise ValueError("Payment instance is required for finishing payment.")
        self._finish_successful_payment(self.payment)

    def _validate_order_status(self):
        if self.order.is_paid:
            raise ValidationError("Pedido já foi pago.")
        if self.order.status == Order.Cancelled:
            raise ValidationError("Pedido cancelado.")

    def _get_order_info(self):
        order_items = self.order.items.all()
        total_price = Decimal(sum(item.get_total_price() for item in order_items))
        return total_price, order_items

    def _create_payment(self):
        payment_method = PaymentMethod.objects.create(
            name='', payment_type=self.payment_type
        )
        return Payment.objects.create(
            customer=self.user,
            order=self.order,
            amount=self.total_price,
            payment_method=payment_method,
        )

    def _process_promotions(self, payment):
        if not self.promo_codes:
            return Decimal(self.total_price)

        promo_code_objs = PromotionCode.objects.filter(code__in=self.promo_codes)
        final_total_price = Decimal(self.total_price)

        for promo_code in promo_code_objs:
            if promo_code in self.valid_promo_codes:
                raise ValidationError(f"Não é possível usar o mesmo cupom múltiplas vezes no mesmo pedido.")

            promo_code.is_valid(self.user)
            final_total_price -= self._apply_discount(promo_code)
            self.valid_promo_codes.append(promo_code)

        PaymentPromotionCode.objects.bulk_create([
            PaymentPromotionCode(payment=payment, promotion_code=code)
            for code in self.valid_promo_codes
        ])
        payment.amount = final_total_price
        return final_total_price

    def _apply_discount(self, promo_code):
        discount = Decimal(0)
        for item in self.order_items:
            discount += promo_code.apply_discount(item.product, item.product.category) * item.quantity
        return discount

    def _update_stock(self):
        for item in self.order_items:
            product = item.product
            stock = getattr(product, 'stock', None)
            if stock and not stock.can_sell(item.quantity):
                raise ValidationError(f"Estoque insuficiente para {item.product.name}.")
            elif stock:
                stock.sell(product=product, quantity=item.quantity)

    def _finalize_payment(self, payment, final_total_price):
        user_balance_check = self.user.pay_with_balance(payment)
        if user_balance_check[0]:
            self.finish_successful_payment(order=self.order, order_items=self.order_items, user=self.user)
        else:
            payment.amount = Decimal(final_total_price - user_balance_check[1])
            payment.save(update_fields=['amount'])
        self._record_payment_creation(payment)

    def _record_payment_creation(self, payment):
        UserHistory.objects.create(
            status=UserHistory.payment_create,
            user=self.user,
            info=f'Criado o pagamento #{payment.id}, do pedido #{payment.order.id}.',
            link=reverse('payments:payment_detail', kwargs={"payment_id": payment.id})
        )

    def _rollback_payment(self, e):
        logger.error(e)
        self.order.status = Order.Cancelled
        self.order.save(update_fields=['status'])
        for item in self.order_items:
            stock = getattr(item.product, 'stock', None)
            if stock:
                stock.restore_hold(item.quantity)
        raise ValidationError('')

    def _finish_successful_payment(self, payment: Payment):
        if payment.status != PaymentStatus.PENDING:
            return

        def handle_role_product(user, product):
            existing_role = Role.objects.filter(user=user, role_type=product.role_type).first()
            if existing_role:
                # Extend or reset role expiration
                existing_role.expires_at = (
                    timezone.now() + product.role_type.effective_days if existing_role.is_expired()
                    else existing_role.expires_at + product.role_type.effective_days)
                existing_role.save(update_fields=['expires_at'])
            else:
                # Create a new role
                Role.objects.create(user=user, role_type=product.role_type)

        try:
            with transaction.atomic():
                user = self.user or payment.customer
                order_items = self.order_items or payment.order.items.select_related(
                    'product', 'product__stock', 'product__role_type').all()

                for item in order_items:
                    product = item.product

                    # Process role products and update stock
                    if product.is_role and not product.is_role_product():
                        raise ValidationError('Este produto não é um cargo, crie outro pedido')
                    elif product.is_role:
                        handle_role_product(user, product)

                    # Update stock for successful sale
                    stock = getattr(product, 'stock', None)
                    if stock:
                        stock.successful_sell(product=product, quantity=item.quantity)

                # Update payment status to completed and mark order as finalized
                payment.status = PaymentStatus.COMPLETED
                payment.save(update_fields=['status'], default_service=True)

                self.order.status = Order.Finalized
                self.order.is_paid = True
                self.order.save(update_fields=['status', 'is_paid'])

                # Clear related cache and log success
                UserHistory.objects.create(
                    status=UserHistory.payment_success,
                    user=user,
                    info=f"Pagamento #{payment.id} efetuado com sucesso.",
                    link=reverse('payments:payment_detail', kwargs={"payment_id": payment.id})
                )
        except Exception as e:
            PaymentService(payment).process_payment_status(items=order_items)
            logger.error(f"Error processing payment status for payment ID {payment.id}: {e}. ")
            raise ValidationError("An error occurred while processing the payment.")
        finally:
            clear_payment_cache(payment.customer)

    def _process_payment_status(self, items=None, new_status=None):
        from orders.models import Order

        def determine_new_status(payment):
            if payment.status == PaymentStatus.COMPLETED:
                return PaymentStatus.REFUNDED
            elif payment.status == PaymentStatus.PENDING:
                return PaymentStatus.CANCELLED
            raise ValidationError(f"Wrong payment status: {payment.status}. It's only possible to update "
                                  f"{PaymentStatus.PENDING} -> {PaymentStatus.CANCELLED} or "
                                  f"{PaymentStatus.COMPLETED} -> {PaymentStatus.REFUNDED}.")

        new_status = new_status or determine_new_status(self.payment)

        try:
            with transaction.atomic():
                # Refund or restore items in order
                order_items = items or self.payment.order.items.select_related('product', 'product__stock',
                                                                          'product__role_type').all()
                for item in order_items:
                    stock = getattr(item.product, 'stock', None)
                    if stock:
                        stock.restore(
                            quantity=item.quantity
                        ) if self.payment.order.status != Order.Waiting_payment else stock.restore_hold(
                            quantity=item.quantity)

                # Update order status to 'cancelled' and mark as unpaid
                self.payment.order.status = Order.Cancelled
                self.payment.order.is_paid = False
                self.payment.order.save(update_fields=['status', 'is_paid'])

                # Handle coupon restoration
                for payment_code in self.payment.used_coupons.all():
                    payment_code.promotion_code.restore_usage(user=self.payment.customer)

                # Update payment status
                self.payment.status = new_status
                self.payment.save(update_fields=['status'], default_service=True)

                # If payment was refunded, refund to user's balance
                if new_status == PaymentStatus.REFUNDED:
                    self.payment.customer.refund_to_balance(self.payment)

        except Exception as e:
            logger.error(f"Error processing payment status for payment ID {self.payment.id}: {e}. "
                         f"Payment status: {self.payment.status}. Trying to change to the payment new status: {
                         new_status}")
            raise ValidationError("An error occurred while processing the payment refund.")
        finally:
            clear_payment_cache(self.payment.customer)


def clear_payment_cache(user):
    cache.delete(payments_cache_key_builder(user.id))


def payments_cache_key_builder(user_id):
    return f'payments_{user_id}_dict'

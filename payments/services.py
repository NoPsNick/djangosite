import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
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

    def __init__(self, payment=None):
        self.payment = payment
        self.user = None
        self.order = None
        self.payment_type = None
        self.promo_codes = None
        self.total_price = None
        self.order_items = None
        self.valid_promo_codes = []
        self.history_to_create = []

    def create_payment(self, user: User, order: Order, payment_type, promo_codes: list = None
                       )-> Payment | Exception | ValidationError :
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
        self.history_to_create = []

        self._validate_order_status()

        try:
            with transaction.atomic():
                self.payment = self._create_payment()
                self._append_user_history(UserHistory.payment_create)
                final_total_price = self._process_promotions()

                self._update_stock()

            self._finalize_payment(final_total_price)

            return self.payment
        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(e)
            self._cancel_payment_order()
            raise

    def process_payment_status(self, new_status=None, items=None, _save=True):
        """
        Updates the status of an existing payment and handles related order and stock adjustments.

        :param _save: IF IT'S FALSE, WILL NOT SAVE IT INTO DB(FOR EXAMPLE EXCLUDED INSTANCES).
        :param new_status: New status to set for the payment.
        :param items: Order items to process (optional, defaults to all items in the order).
        """
        if not self.payment:
            raise ValueError("Payment instance is required for processing status.")
        self._process_payment_status(items=items, new_status=new_status, _save=_save)

    def finish_successful_payment(self):
        """
        Completes the payment process, handling role products and finalizing the order.
        """
        if not self.payment:
            raise ValueError("Payment instance is required for finishing payment.")
        return self._finish_successful_payment()

    def _validate_order_status(self):
        if self.order.is_paid:
            raise ValidationError("Pedido já foi pago.")
        if self.order.status == Order.Cancelled:
            raise ValidationError("Pedido cancelado.")

    def _get_order_info(self):
        order_items = self.order.items.all()
        total_price = sum(item.get_total_price() for item in order_items)
        return Decimal(total_price), order_items

    def _create_payment(self):
        payment_method = PaymentMethod.objects.create(
            name='', payment_type=self.payment_type
        )
        payment = Payment(
            status=PaymentStatus.PENDING,
            customer=self.user,
            order=self.order,
            amount=self.total_price,
            payment_method=payment_method,
        )
        # Para não causar problemas é criado um objeto primeiro depois salva o objeto com o default_service
        payment.save(default_service=True)
        return payment

    def _process_promotions(self):
        """
            Applies valid promotions to the payment, adjusting the final price.

            :return: The adjusted total price after applying promotions.
        """
        if not self.promo_codes:
            return Decimal(self.total_price)

        promo_code_objs = PromotionCode.objects.filter(code__in=self.promo_codes).select_related('product')
        final_total_price = Decimal(self.total_price)

        for promo_code in promo_code_objs:
            promo_code.is_valid(self.user)
            final_total_price -= self._apply_discount(promo_code)
            self.valid_promo_codes.append(promo_code)

        PaymentPromotionCode.objects.bulk_create([
            PaymentPromotionCode(payment=self.payment, promotion_code=code)
            for code in self.valid_promo_codes
        ])
        if self.payment.amount != final_total_price:
            self.payment.amount = final_total_price
            self.payment.save(update_fields=['amount'], default_service=True)
        return final_total_price

    def _apply_discount(self, promo_code: PromotionCode):
        discount = Decimal(0)
        for item in self.order_items:
            discount += (item.product.price - promo_code.apply_discount(item.product)) * item.quantity
        return discount

    def _update_stock(self):
        for item in self.order_items:
            stock = getattr(item.product, 'stock', None)
            if stock:
                if not stock.can_sell(item.quantity):
                    self._cancel_payment_order()
                    raise ValidationError(f"O produto {item.product.name}, não está disponível no momento.")
                stock.sell(product=item.product, quantity=item.quantity)

    def _finalize_payment(self, final_total_price):
        user_balance_check = self.user.pay_with_balance(self.payment)
        if user_balance_check[0]:
            self.history_to_create.append(user_balance_check[1])
            self.finish_successful_payment()
        elif Decimal(self.payment.amount) != Decimal(final_total_price - user_balance_check[1]):
            self.payment.amount = Decimal(final_total_price - user_balance_check[1])
            self.payment.save(update_fields=['amount'], default_service=True)

    def _append_user_history(self, user_history_type, user=None):
        user_history_infos = {
            UserHistory.payment_create: f'Criado o pagamento #{self.payment.id}, do pedido #{self.payment.order_id}.',
            UserHistory.payment_success: f'Pagamento #{self.payment.id}, do pedido #{self.payment.order_id},'
                                         f' finalizado com sucesso.',
            UserHistory.payment_fail: f'Pagamento #{self.payment.id} falhou.'
        }
        history = UserHistory(
            type=user_history_type,
            user=user or self.user,
            info=user_history_infos[user_history_type],
            link=reverse('payments:payment_detail', kwargs={"payment_id": self.payment.id})
        )

        self.history_to_create.append(history)

    def _cancel_payment_order(self):
        order = self.order or self.payment.order
        order.status = Order.Cancelled
        order.save(update_fields=['status'])

    @staticmethod
    def _process_role_product(user, product):
        """
        Handles assigning or extending roles for role products.
        """
        existing_role = Role.objects.filter(user=user, role_type=product.role_type).first()
        if existing_role:
            if existing_role.is_expired():
                existing_role.expires_at = timezone.now() + product.role_type.effective_days
            else:
                existing_role.expires_at += product.role_type.effective_days
            existing_role.save(update_fields=['expires_at'])
        else:
            Role.objects.create(user=user, role_type=product.role_type)

    def _finish_successful_payment(self):
        """
        Completes a successful payment, handling role products and finalizing the order.
        """
        if self.payment.status != PaymentStatus.PENDING:
            raise ValueError("Cannot finalize a non-pending payment.")

        try:
            with transaction.atomic():
                user = self.user or self.payment.customer
                order = self.order or self.payment.order
                self._finalize_order_and_payment(order)
                order_items = self.order_items or order.items.select_related(
                    'product', 'product__stock', 'product__role_type').all()

                for item in order_items:
                    product = item.product

                    if product.is_role:
                        if not product.is_role_product():
                            raise Exception(f'The {product.slug} is marked as a role, but its not')
                        self._process_role_product(user, product)

                    stock = getattr(product, 'stock', None)
                    if stock:
                        stock.successful_sell(product=product, quantity=item.quantity)
        except Exception as e:
            logger.error(f"Error finalizing payment {self.payment.id}: {e}")
            self.process_payment_status(items=order_items, new_status=PaymentStatus.REFUNDED)
            raise ValidationError("An error occurred while processing the payment.")

    def _finalize_order_and_payment(self, order):
        """
        Marks the payment as completed and finalizes the associated order.
        """
        self.payment.status = PaymentStatus.COMPLETED
        self.payment.save(update_fields=['status'], default_service=True)

        order.status = order.Finalized
        order.is_paid = True
        order.save(update_fields=['status', 'is_paid'])

        self._append_user_history(UserHistory.payment_success, user=order.customer)


    def _process_payment_status(self, items=None, new_status=None, _save=True):
        from orders.models import Order

        def determine_new_status(payment):
            if payment.status == PaymentStatus.COMPLETED:
                return PaymentStatus.REFUNDED
            elif payment.status == PaymentStatus.PENDING:
                return PaymentStatus.CANCELLED
            raise Exception(f"Wrong payment status: {payment.status}. It's only possible to update "
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

                if _save:
                    # Update payment status
                    self.payment.status = new_status
                    self.payment.save(update_fields=['status'], default_service=True)

                # If payment was refunded, refund to user's balance
                if new_status == PaymentStatus.REFUNDED:
                    refund_history = self.payment.customer.refund_to_balance(self.payment)
                    self.history_to_create.append(refund_history)
                elif new_status == PaymentStatus.FAILED:
                    self._append_user_history(UserHistory.payment_fail, user=self.payment.customer)

        except Exception as e:
            logger.error(f"Error processing payment status for payment ID {self.payment.id}: {e}. "
                         f"Payment status: {self.payment.status}. Trying to change to the payment new status: {
                         new_status}")
            raise ValidationError("An error occurred while processing the payment refund.")

    def bulk_create_histories(self):
        UserHistory.objects.bulk_create(self.history_to_create)
        self.history_to_create = []


def payments_cache_key_builder(user_id):
    return f'payments_{user_id}_dict'

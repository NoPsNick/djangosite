from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from decimal import Decimal

from model_utils.models import TimeStampedModel, SoftDeletableModel

from orders.models import Order
from payments.managers import PaymentManager
from products.models import PromotionCode

User = get_user_model()


class ExternalApiResponse(TimeStampedModel):
    """Model to store responses from external APIs."""
    transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Transaction ID",
        db_index=True
    )
    response_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Response for Transaction {self.transaction_id}"

    class Meta:
        verbose_name = "External API Response"
        verbose_name_plural = "External API Responses"


class PaymentMethod(TimeStampedModel):
    """Model representing a method of payment."""
    PAYMENT_TYPE_CHOICES = [
        ('user_balance', 'Saldo do Usuário'),
        ('credit_card', 'Cartão de Crédito'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Transferência Bancária'),
    ]

    name = models.CharField(verbose_name="Nome do Cliente",
                            max_length=100,
                            db_index=True,
                            blank=True,
                            null=True, )
    payment_type = models.CharField(
        verbose_name="Tipo de pagamento",
        max_length=100,
        choices=PAYMENT_TYPE_CHOICES,
        default='user_balance',
    )
    response = models.ForeignKey(
        ExternalApiResponse,
        verbose_name="External API Response",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payment_methods"
    )

    class Meta:
        verbose_name = "Método de pagamento"
        verbose_name_plural = "Métodos de pagamento"
        indexes = [
            models.Index(fields=['payment_type']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"Método de pagamento {self.name or self.payment_type}"


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    COMPLETED = 'completed', 'Completo'
    FAILED = 'failed', 'Falhou'
    REFUNDED = 'refunded', 'Reembolsado'
    CANCELLED = 'cancelled', 'Cancelado'


class Payment(TimeStampedModel, SoftDeletableModel):
    """Model representing a payment made by a user."""
    customer = models.ForeignKey(
        User,
        related_name="payments",
        verbose_name="Cliente",
        on_delete=models.SET_NULL,
        null=True
    )
    order = models.ForeignKey(
        Order,
        related_name="payments",
        verbose_name="Pedido",
        on_delete=models.SET_NULL,
        null=True
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        verbose_name="Método de pagamento",
        related_name="payments",
        on_delete=models.PROTECT
    )
    amount = models.DecimalField(
        verbose_name="Preço total",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('999.99'))]
    )
    status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Estado do pagamento"
    )
    used_coupons = models.ManyToManyField(
        PromotionCode,
        through='PaymentPromotionCode',
        verbose_name="Cupons aplicados",
        related_name='payments',
        blank=True
    )

    objects = PaymentManager()

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['order']),
            models.Index(fields=['modified']),
        ]

    def __str__(self):
        return f'Pagamento #{self.id}'

    def clean(self):
        super().clean()
        if self.amount <= 0:
            raise ValidationError('The payment amount must be positive.')
        self.verify()

    def verify(self):
        if self.pk:
            previous_status = Payment.objects.get(pk=self.pk).status
            if self.status == PaymentStatus.PENDING and previous_status == PaymentStatus.COMPLETED:
                raise ValidationError('You cannot change a "COMPLETED" payment to "PENDING".')
            if self.status != previous_status and previous_status in {PaymentStatus.FAILED, PaymentStatus.REFUNDED}:
                raise ValidationError('You cannot change a "FAILED" or "REFUNDED" payment status.')

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = Payment.objects.get(pk=self.pk).status

        # Standard save with default_service or new changes
        if kwargs.pop('default_service', False):
            super().save(*args, **kwargs)
            return

        # Handle status transitions if status has changed
        if previous_status != self.status:
            from payments.services import finish_successful_payment, process_payment_status
            if previous_status == PaymentStatus.PENDING and self.status == PaymentStatus.COMPLETED:
                payment = Payment.objects.select_for_update().get(id=self.id)
                try:
                    finish_successful_payment(payment)
                except Exception as e:
                    raise ValidationError(str(e))
            elif previous_status == PaymentStatus.COMPLETED and self.status == PaymentStatus.REFUNDED:
                payment = Payment.objects.select_for_update().get(id=self.id)
                try:
                    process_payment_status(payment)
                except Exception as e:
                    raise ValidationError(str(e))
            elif previous_status == PaymentStatus.PENDING and (self.status == PaymentStatus.CANCELLED
                                                               or self.status == PaymentStatus.FAILED):
                payment = Payment.objects.select_for_update().get(id=self.id)
                try:
                    process_payment_status(payment, new_status=self.status)
                except Exception as e:
                    raise ValidationError(str(e))

        # Execute the standard save if no service transition occurred
        super().save(*args, **kwargs)


class PaymentPromotionCode(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="promotion_codes"
    )
    promotion_code = models.ForeignKey(
        PromotionCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Promotion Code"
        verbose_name_plural = "Payment Promotion Codes"
        indexes = [
            models.Index(fields=['payment', 'promotion_code']),
        ]

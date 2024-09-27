from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from decimal import Decimal

from model_utils.models import TimeStampedModel, SoftDeletableModel

from orders.models import Order
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
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        # Add more as needed
    ]

    payment_type = models.CharField(
        verbose_name="Payment Type",
        max_length=100,
        choices=PAYMENT_TYPE_CHOICES,
        default='credit_card',
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
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        indexes = [
            models.Index(fields=['payment_type']),
        ]


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'


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
        on_delete=models.SET_NULL,
        null=True
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        verbose_name="Payment Method",
        related_name="payments",
        on_delete=models.PROTECT
    )
    amount = models.DecimalField(
        verbose_name="Total Amount",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('999.99'))]
    )
    status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Payment Status"
    )
    used_coupons = models.ManyToManyField(
        PromotionCode,
        through='PaymentPromotionCode',
        verbose_name="Applied Coupons",
        related_name='payments',
        blank=True
    )

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
        ]

    def clean(self):
        super().clean()
        if self.amount <= 0:
            raise ValidationError('The payment amount must be positive.')

    def refund(self):
        """Process a refund for the payment."""
        if self.status == PaymentStatus.COMPLETED:
            self.status = PaymentStatus.REFUNDED
            self.save(update_fields=['status'])


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

from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from decimal import Decimal

from model_utils.models import TimeStampedModel, StatusModel

from orders.managers import OrderManager
from products.models import Product, PromotionCode
from users.models import RoleType

User = get_user_model()


class Order(TimeStampedModel):
    Cancelled = "cancelado"
    Waiting_payment = "aguardando"
    Finalized = "finalizado"

    status_choices = [
        (Waiting_payment, "Aguardando pagamento"),
        (Finalized, "Finalizado"),
        (Cancelled, "Pedido cancelado"),
    ]

    customer = models.ForeignKey(User, related_name="pedidos", verbose_name="Cliente", on_delete=models.PROTECT)
    status = models.CharField(verbose_name='Estado do pedido', choices=status_choices, default=Waiting_payment,
                              max_length=50)
    is_paid = models.BooleanField(verbose_name="Foi pago?", default=False)

    objects = OrderManager()

    class Meta:
        ordering = ["-modified"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['modified']),
            models.Index(fields=['is_paid']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"

    def get_total_amount(self):
        return Decimal(sum(item.get_total_price() for item in self.items.all()))  # Sum the total for all items


class Item(models.Model):
    order = models.ForeignKey(Order, verbose_name="Pedido", related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Produto", related_name="order_items", on_delete=models.CASCADE)
    price = models.DecimalField(verbose_name='Preço', max_digits=10, decimal_places=2, default=0, blank=True,
                                null=True)
    name = models.CharField(verbose_name='Nome do produto', max_length=50, default="", blank=True, null=True)
    slug = models.CharField(verbose_name='Slug do produto', max_length=50, default="", blank=True, null=True)
    quantity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(settings.CART_ITEM_MAX_QUANTITY),
        ]
    )

    class Meta:
        verbose_name = "produto de pedido"
        verbose_name_plural = "produdos de pedidos"

        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"Item {self.name or self.product.name} (Quantity: {self.quantity})"

    def get_total_price(self):
        if self.price:
            return Decimal(self.price * self.quantity)
        return Decimal(self.product.price * self.quantity)

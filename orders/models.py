from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from decimal import Decimal

from model_utils.models import TimeStampedModel, StatusModel
from model_utils import Choices

from orders.managers import OrderManager
from products.models import Product, PromotionCode

User = get_user_model()


class Order(TimeStampedModel, StatusModel):
    Cancelled = "Cancelado"
    Waiting_payment = "Aguardando pagamento"
    Finalized = "Finalizado"

    STATUS = Choices(
        (Waiting_payment, "Aguardando pagamento"),
        (Finalized, "Finalizado"),
        (Cancelled, "Pedido cancelado"),
    )

    customer = models.ForeignKey(User, related_name="pedidos", verbose_name="Cliente", on_delete=models.PROTECT)
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
        return f"Item {self.product.name} (Quantity: {self.quantity})"

    def get_total_price(self):
        return Decimal(self.product.price * self.quantity)

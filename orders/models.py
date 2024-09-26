from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from model_utils.models import TimeStampedModel, StatusModel
from model_utils import Choices

from decimal import Decimal

from products.models import Product, PromotionCode

User = get_user_model()

class Order(TimeStampedModel, StatusModel):
    Cancelado = "Cancelado"
    Caminho = "A caminho"
    Aguardando = "Aguardando pagamento"
    Finalizado = "Finalizado"
    Vender = "Vender"
    Cancelar = "Cancelar Venda"

    STATUS = Choices(
        (Caminho, "A caminho"),
        (Aguardando, "Aguardando pagamento"),
        (Finalizado, "Finalizado"),
        (Cancelado, "Pedido cancelado"),
    )

    customer = models.ForeignKey(User, related_name="pedidos", verbose_name="Cliente", on_delete=models.PROTECT)
    is_paid = models.BooleanField(verbose_name="Foi pago?", default=False)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"

    def get_total_amount(self):
        return sum(item.get_total_price() for item in self.items.all())  # Sum the total for all items

class Item(models.Model):
    order = models.ForeignKey(Order, verbose_name="Pedido", related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Produto", related_name="order_items", on_delete=models.CASCADE)
    promotion_code = models.ForeignKey(PromotionCode, verbose_name="Código promocional", related_name="used_code",
                                       on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(settings.CART_ITEM_MAX_QUANTITY),
        ]
    )

    class Meta:
        verbose_name = "produto de pedido"
        verbose_name_plural = "produdos de pedidos"

    def __str__(self):
        return f"Item {self.product.name} (Quantity: {self.quantity})"

    def get_total_price(self):
        if not self.promotion_code:
            return self.product.price * self.quantity
        else:
            return Decimal(self.promotion_code.apply_discount(product=self.product, category=self.product.category
                                                          )) * self.quantity

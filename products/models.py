
from django.db import models, transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel, StatusModel

from .managers import EstoqueManager, AvailableManager


class Category(TimeStampedModel):
    name = models.CharField("Nome", max_length=255, unique=True)
    slug = AutoSlugField(unique=True, always_update=True, populate_from="name")

    class Meta:
        ordering = ("name",)
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField("Nome", max_length=255)
    slug = AutoSlugField(unique=True, always_update=True, populate_from="name")
    image = models.ImageField("Imagem", upload_to="products/%Y/%m/%d", blank=True)
    description = models.TextField("Descrição", blank=True)
    price = models.DecimalField("Preço", max_digits=10, decimal_places=2)
    is_available = models.BooleanField("Está disponível?", default=True)

    objects = models.Manager()
    available = AvailableManager()

    class Meta:
        ordering = ("-created",)
        verbose_name = "produto"
        verbose_name_plural = "produtos"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"slug": self.slug})


class Stock(TimeStampedModel):
    product = models.OneToOneField(
        Product, related_name="estoque", on_delete=models.CASCADE, unique=True
    )
    units = models.PositiveIntegerField(
        default=0,
        verbose_name="Unidades em estoque",
        help_text="Quantidade disponível no estoque.",
    )
    units_sold = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade vendida",
        help_text="Quantidade de unidades vendidas.",
    )

    objects = EstoqueManager()

    class Meta:
        ordering = ("-created",)
        verbose_name = "estoque"
        verbose_name_plural = "estoques"

    def __str__(self):
        return f"{self.product.name} - {self.units} unidades"

    def save(self, *args, **kwargs):
        # Update product availability based on stock
        self.product.is_available = self.units > 0
        self.product.save(update_fields=['is_available'])
        super().save(*args, **kwargs)
        # Update product cache since availability changed

    def can_sell(self, quantidade=1):
        """Check if there is enough stock to sell."""
        return self.units >= quantidade

    @transaction.atomic
    def sell(self, quantidade=1):
        """
        Safely reduce stock and increase units_sold using transaction.atomic
        and select_for_update to avoid race conditions.
        """
        stock = Stock.objects.select_for_update().get(id=self.id)

        if not stock.can_sell(quantidade):
            raise ValidationError("Not enough stock available.")

        # Update the stock and units sold atomically
        stock.units = F('units') - quantidade
        stock.units_sold = F('units_sold') + quantidade
        stock.save(update_fields=['units', 'units_sold'])

        # Update product cache

        return True

    @transaction.atomic
    def restore(self, quantidade=1):
        """
        Safely restore stock and reduce units_sold using transaction.atomic
        and select_for_update to avoid race conditions.
        """
        stock = Stock.objects.select_for_update().get(id=self.id)

        # Restore units and adjust units_sold atomically
        stock.units = F('units') + quantidade
        stock.units_sold = F('units_sold') - quantidade
        stock.save(update_fields=['units', 'units_sold'])

        # Update product cache


class Promotion(StatusModel, TimeStampedModel):
    EXPIRADO = "Expirado"
    ATIVO = "Ativo"
    PENDENTE = "Pendente"

    STATUS_CHOICES = [
        (EXPIRADO, "Expirado"),
        (ATIVO, "Ativo"),
        (PENDENTE, "Pendente"),
    ]

    starts_at = models.DateTimeField("Data do começo")
    expires_at = models.DateTimeField("Data do fim")
    product = models.ForeignKey(Product, verbose_name="Produto", related_name="promotion", on_delete=models.CASCADE, to_field='slug')
    status = models.CharField("Estado", max_length=10, choices=STATUS_CHOICES, default=EXPIRADO)
    changed_price = models.DecimalField("Preço em promoção", max_digits=10, decimal_places=2)
    original_price = models.DecimalField("Preço original", max_digits=10, decimal_places=2, blank=True, null=True)

    def clean(self):
        if not self.original_price:
            self.original_price = self.product.price
            if self.original_price != self.product.price:
                raise ValidationError("Cannot create a promotion that the original price is different "
                                      "from the product price.")

        if not self.product.is_available:
            raise ValidationError("Cannot create a promotion for an unavailable product.")

        if self.original_price < self.changed_price:
            raise ValidationError("Cannot create a promotion that the changed price is higher than the original price.")

    def save(self, *args, **kwargs):
        if not self.original_price:
            self.original_price = self.product.price

        now = timezone.now()
        if self.expires_at and now > self.expires_at:
            self.status = self.EXPIRADO
            # Revert product price to original price if the promotion has expired
            self.product.price = self.original_price
            self.product.save(update_fields=['price'])

        elif self.starts_at and now >= self.starts_at:
            self.status = self.ATIVO
            self.product.price = self.changed_price
            self.product.save(update_fields=['price'])

        else:
            self.status = self.PENDENTE

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Promoção do produto {self.product.name} - {self.status}"

    class Meta:
        ordering = ("-created",)
        verbose_name = "promoção"
        verbose_name_plural = "promoções"

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel, StatusModel

from .managers import AvailableManager

User = get_user_model()

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

    class Meta:
        ordering = ("-created",)
        verbose_name = "estoque"
        verbose_name_plural = "estoques"

    def __str__(self):
        return f"{self.product.name} - {self.units} unidades"

    def save(self, *args, **kwargs):
        from .services import update_product_cache
        # Update product availability based on stock
        self.product.is_available = self.units > 0
        self.product.save(update_fields=['is_available'])
        super().save(*args, **kwargs)
        # Update product cache since availability changed
        update_product_cache(None, self.product)

    def can_sell(self, quantidade=1):
        """Check if there is enough stock to sell."""
        return self.units >= quantidade

    @transaction.atomic
    def sell(self, quantidade=1):
        from .services import update_product_cache
        """
        Safely reduce stock and increase units_sold using "transaction.atomic"
        and select_for_update to avoid race conditions.
        """
        stock = Stock.objects.select_for_update().get(id=self.id)

        if not stock.can_sell(quantidade):
            raise ValidationError("Not enough stock available.")

        # Update the stock and units sold atomically
        stock.units = F('units') - quantidade
        stock.units_sold = F('units_sold') + quantidade
        stock.save(update_fields=['units', 'units_sold'])

        # Only update cache after transaction is committed
        transaction.on_commit(lambda: update_product_cache(None, self.product))

        return True

    @transaction.atomic
    def restore(self, quantidade=1):
        from .services import update_product_cache
        """
        Safely restore stock and reduce units_sold using "transaction.atomic"
        and select_for_update to avoid race conditions.
        """
        stock = Stock.objects.select_for_update().get(id=self.id)

        # Restore units and adjust units_sold atomically
        stock.units = F('units') + quantidade
        stock.units_sold = F('units_sold') - quantidade
        stock.save(update_fields=['units', 'units_sold'])

        # Only update cache after transaction is committed
        transaction.on_commit(lambda: update_product_cache(None, self.product))

        return True


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
    product = models.ForeignKey(Product, verbose_name="Produto", related_name="promotion", on_delete=models.CASCADE,
                                to_field='slug')
    status = models.CharField("Estado", max_length=10, choices=STATUS_CHOICES, default=EXPIRADO)
    changed_price = models.DecimalField("Preço em promoção", max_digits=10, decimal_places=2)
    original_price = models.DecimalField("Preço original", max_digits=10, decimal_places=2, blank=True,
                                         null=True)

    def clean(self):
        if not self.original_price:
            self.original_price = self.product.price

            if self.original_price != self.product.price:
                raise ValidationError("Cannot create a promotion that the original price is different "
                                      "from the product price.")

        if not self.product.is_available:
            raise ValidationError("Cannot create a promotion for an unavailable product.")

        if self.original_price < self.changed_price:
            raise ValidationError("Cannot create a promotion that the changed price is higher than the original"
                                  " price.")

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


class PromotionCode(TimeStampedModel):
    user = models.ForeignKey(
        User, verbose_name="Usuário", on_delete=models.PROTECT, related_name='promotion_codes',
        blank=True, null=True
    )
    code = models.CharField("Código", max_length=50, unique=True)
    status = models.BooleanField("Está ativo?", default=True)
    product = models.ForeignKey(
        'Product', verbose_name="Produto", on_delete=models.CASCADE,
        related_name='promotion_codes', null=True, blank=True
    )
    category = models.ForeignKey(
        'Category', verbose_name="Categoria", on_delete=models.CASCADE,
        related_name='promotion_codes', null=True, blank=True
    )
    can_with_promotion = models.BooleanField("Pode ser usado com outra promoção?", default=False)
    discount_amount = models.DecimalField("Valor do desconto", max_digits=10, decimal_places=2, null=True,
                                          blank=True)
    discount_percentage = models.DecimalField("Porcentagem de desconto", max_digits=5, decimal_places=2,
                                              null=True,
                                              blank=True)
    usage_limit = models.PositiveIntegerField("Limite de uso global", default=1)
    usage_count = models.PositiveIntegerField("Contagem de uso global", default=0)
    user_usage_limit = models.PositiveIntegerField("Limite de uso por usuário", default=1)
    start_at = models.DateTimeField("Início da validade", null=True, blank=True)
    expires_at = models.DateTimeField("Expira em", null=True, blank=True)

    class Meta:
        ordering = ['-created']
        verbose_name = "Código Promocional"
        verbose_name_plural = "Códigos Promocionais"

    def __str__(self):
        return self.code

    def is_valid(self, user=None):
        """
        Check if the promotion code is valid for use.
        Optional user argument for checking per-user usage limit.
        """
        # Check if the code is enabled
        if not self.status:
            raise ValidationError("This promotion code is disabled.")

        # Check if the promotion has started
        if self.start_at and timezone.now() < self.start_at:
            raise ValidationError("This promotion code is not yet valid.")

        # Check if the promotion has expired
        if self.expires_at and timezone.now() > self.expires_at:
            raise ValidationError("This promotion code has expired.")

        # Check if the code has reached the global usage limit
        if self.usage_limit and self.usage_count >= self.usage_limit:
            raise ValidationError("This promotion code has reached its usage limit.")

        # Check the per-user usage limit
        if user:
            user_code_usage = PromotionCodeUsage.objects.filter(user=user, promotion_code=self).count()
            if user_code_usage.exists() and user_code_usage >= self.user_usage_limit:
                raise ValidationError(f"This promotion code has reached its usage limit for user {user.username}.")

        return True

    def apply_discount(self, product, category=None):
        """
        Apply the discount to a product. Returns the discounted price.
        """
        # Check if the code is applicable to the product or category
        if self.product and self.product != product:
            raise ValidationError("This promotion code cannot be used for this product.")

        if self.category and (not category or self.category != category):
            raise ValidationError("This promotion code cannot be used for this category.")

        if product.promotion.exists() and not self.can_with_promotion:
            raise ValidationError("This product already has an active promotion and this code cannot be applied.")

        # Apply the discount (either fixed amount or percentage)
        if self.discount_amount:
            return max(product.price - self.discount_amount, 0)
        elif self.discount_percentage:
            discount = (self.discount_percentage / 100) * product.price
            return max(product.price - discount, 0)
        else:
            raise ValidationError("No valid discount available for this code.")

    def increment_usage(self, user=None):
        """
        Increment the usage count of the promotion code.
        Optionally track per-user usage if a user is provided.
        """
        # Increment global usage count
        self.usage_count = F('usage_count') + 1
        self.save(update_fields=['usage_count'])

        # Track usage for the user
        if user:
            PromotionCodeUsage.objects.create(user=user, promotion_code=self)


class PromotionCodeUsage(models.Model):
    """
    Tracks how many times a specific user has used a promotion code.
    """
    user = models.ForeignKey(User, verbose_name="Usuário", on_delete=models.PROTECT)
    promotion_code = models.ForeignKey(PromotionCode, verbose_name="Código Promocional", on_delete=models.PROTECT)
    used_at = models.DateTimeField("Usado em", auto_now_add=True)

    class Meta:
        unique_together = ('user', 'promotion_code')
        verbose_name = "Uso do Código Promocional"
        verbose_name_plural = "Usos de Códigos Promocionais"

    def __str__(self):
        return f"{self.user} usou {self.promotion_code}"

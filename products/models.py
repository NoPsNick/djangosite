from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel, StatusModel

from .managers import AvailableManager
from users.models import RoleType

User = get_user_model()


class Category(TimeStampedModel):
    name = models.CharField("Nome", max_length=255, unique=True)
    slug = AutoSlugField(unique=True, always_update=True, populate_from="name")

    class Meta:
        ordering = ("name",)
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE, null=True, blank=True
    )
    role_type = models.ForeignKey(RoleType, related_name="selling_roles", null=True, blank=True,
                                  on_delete=models.CASCADE)
    is_role = models.BooleanField(default=False)
    name = models.CharField("Nome", max_length=255)
    slug = AutoSlugField(unique=True, always_update=True, populate_from="name")
    image = models.ImageField("Imagem", upload_to="products/%Y/%m/%d", blank=True)
    description = models.TextField("Descrição", blank=True)
    price = models.DecimalField("Preço", max_digits=10, decimal_places=2)
    is_available = models.BooleanField("Está disponível?", default=True)

    objects = models.Manager()
    available = AvailableManager()

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"

        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_available']),
            models.Index(fields=['price']),
        ]

        constraints = [
            # Impedir que produto tenha ambos (role_type e category) ou nenhum
            models.CheckConstraint(
                check=(
                        models.Q(category__isnull=False, role_type__isnull=True) |
                        models.Q(category__isnull=True, role_type__isnull=False)
                ),
                name="category_or_role_type"
            ),
            # Garante que 'role_type' só pode existir se is_role for True e vice-versa
            models.CheckConstraint(
                check=models.Q(is_role=True, role_type__isnull=False) | models.Q(is_role=False, role_type__isnull=True),
                name="role_type_consistency"
            ),
        ]

    def is_role_product(self):
        """
        Verifica se este produto está relacionado a um RoleType, ou seja, é um produto que corresponde a um cargo.
        """
        return self.role_type is not None

    def clean(self):
        super().clean()

        # Verifica se o produto é um role e garante que 'role_type' seja obrigatório
        if self.is_role and not self.role_type:
            raise ValidationError("Um produto do tipo 'cargo' deve ter um RoleType associado.")

        # Caso contrário, se o produto não for 'cargo', o 'role_type' deve ser nulo
        if not self.is_role and self.role_type:
            raise ValidationError("Somente produtos do tipo 'cargo' podem ter um RoleType.")

        # Um produto não pode ter ambos, categoria e 'role_type'
        if self.role_type and self.category:
            raise ValidationError("Um produto só pode ter um cargo OU categoria, não ambos.")

        # Verificação adicional do 'role_type'
        if self.role_type:
            if self.role_type.staff:
                raise ValidationError("Um produto não poder ser um cargo de staff")
            # Preço, Nome e Descrição do produto serão iguais às do RoleType
            self.price = self.role_type.price
            self.name = self.role_type.name
            self.description = self.role_type.description

        # Um produto não pode ficar sem category OU sem 'role_type', sendo obrigatório ter um
        if not self.role_type and not self.category:
            raise ValidationError("Um produto precisa ter uma catergoria OU um cargo, não ambos, mas obrigatório"
                                  "um deles.")

    def save(self, *args, **kwargs):
        # Chamamos clean para garantir que as validações sejam aplicadas
        self.clean()
        self.is_role = self.is_role_product()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"slug": self.slug})

    def check_not_updated_promotions(self):
        """Check if any active promotions are valid and raise a ValidationError if not."""
        now = timezone.now()  # Get the current time in the correct timezone
        outdated_promotions = []

        # Filter for active promotions and check their validity
        for promotion in self.promotions.filter(active=True):
            if not (promotion.starts_at <= now < promotion.expires_at):
                # Only save if promotion state is outdated
                if promotion.expires_at <= now:
                    outdated_promotions.append(promotion)
                    promotion.save()  # Save to update the promotion if necessary

        if outdated_promotions:
            # Raise an error if there are outdated promotions
            raise ValidationError(
                f"The following promotions are outdated: {', '.join([promo.name for promo in outdated_promotions])}"
            )

        return True  # All promotions are valid, or no promotion was found


class Stock(TimeStampedModel):
    product = models.OneToOneField(
        Product, related_name="stock", on_delete=models.CASCADE
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

    units_hold = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade vendida em estágio de confirmação",
        help_text="Quantidade de unidades vendidas que o pagamento não foi confirmado ainda.",
    )

    class Meta:
        ordering = ("-created",)
        verbose_name = "estoque"
        verbose_name_plural = "estoques"

        indexes = [
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.units} unidades"

    def save(self, *args, **kwargs):
        from .services import update_product_cache

        # Update product availability based on stock
        try:
            updated_stock = Stock.objects.select_for_update().get(id=self.id)
        except Stock.DoesNotExist:
            updated_stock = self

        self.product.is_available = updated_stock.units > 0
        self.product.save(update_fields=['is_available'])
        super().save(*args, **kwargs)
        # Update product cache since availability changed
        update_product_cache(sender=self, instance=self.product)

    def can_sell(self, quantity=1):
        """Check if there is enough stock to sell."""
        return self.units >= quantity

    @transaction.atomic
    def sell(self, quantity=1):
        from .services import update_product_cache
        """
        Safely reduce stock and increase units_sold using "transaction.atomic"
        and select_for_update to avoid race conditions.
        """
        stock = Stock.objects.select_for_update().get(id=self.id)

        if not stock.can_sell(quantity):
            raise ValidationError("Not enough stock available.")

        # Update the stock and units sold atomically
        stock.units = F('units') - quantity
        stock.units_hold = F('units_hold') + quantity
        stock.save(update_fields=['units', 'units_hold'])

        # After the update, fetch the updated units from the database
        updated_stock = Stock.objects.get(id=stock.id)
        available_units = updated_stock.units

        # Set product availability based on the updated units
        stock.product.is_available = available_units > 0
        stock.product.save(update_fields=['is_available'])

        # Only update cache after transaction is committed
        transaction.on_commit(lambda: update_product_cache(sender=updated_stock, instance=updated_stock.product))

    @transaction.atomic()
    def successful_sell(self, quantity=1):
        from .services import update_product_cache
        """
        Safely reduce stock units_hold and increase units_sold using "transaction.atomic"
        and select_for_update to avoid race conditions.
        """
        stock = Stock.objects.select_for_update().get(id=self.id)

        # Update the stock's units_sold and units_hold atomically
        stock.units_sold = F('units_sold') + quantity
        stock.units_hold = F('units_hold') - quantity
        stock.save(update_fields=['units_sold', 'units_hold'])

        # After the update, fetch the updated units from the database
        updated_stock = Stock.objects.get(id=stock.id)
        available_units = updated_stock.units

        # Set product availability based on the updated units
        stock.product.is_available = available_units > 0
        stock.product.save(update_fields=['is_available'])

        # Only update cache after transaction is committed
        transaction.on_commit(lambda: update_product_cache(sender=updated_stock, instance=updated_stock.product))

    @transaction.atomic
    def restore(self, quantity=1):
        from .services import update_product_cache
        """
        Safely restore stock and reduce units_sold using "transaction.atomic"
        and select_for_update to avoid race conditions.
        """
        stock = Stock.objects.select_for_update().get(id=self.id)

        # Restore units and adjust units_sold atomically
        stock.units = F('units') + quantity
        stock.units_sold = F('units_sold') - quantity
        stock.save(update_fields=['units', 'units_sold'])

        # Only update cache after transaction is committed
        transaction.on_commit(lambda: update_product_cache(sender=self, instance=self.product))

    @transaction.atomic
    def restore_hold(self, quantity=1):
        from .services import update_product_cache
        """
        Safely restore stock and reduce units_sold using "transaction.atomic"
        and select_for_update to avoid race conditions.
        """
        stock = Stock.objects.select_for_update().get(id=self.id)

        # Restore units and adjust units_sold atomically
        stock.units = F('units') + quantity
        stock.units_sold = F('units_hold') - quantity
        stock.save(update_fields=['units', 'units_hold'])

        # Only update cache after transaction is committed
        transaction.on_commit(lambda: update_product_cache(sender=self, instance=self.product))


class Promotion(StatusModel, TimeStampedModel):
    EXPIRADO = "Expirado"
    ATIVO = "Ativo"
    PENDENTE = "Pendente"

    STATUS_CHOICES = [
        (EXPIRADO, "Expirado"),
        (ATIVO, "Ativo"),
        (PENDENTE, "Pendente"),
    ]

    name = models.CharField("Nome", max_length=255, unique=True)
    description = models.TextField("Descrição", max_length=255, blank=True, null=True)
    starts_at = models.DateTimeField("Data do começo")
    expires_at = models.DateTimeField("Data do fim")
    product = models.ForeignKey(Product, verbose_name="Produto", related_name="promotions", on_delete=models.CASCADE,
                                to_field='slug')
    status = models.CharField("Estado", max_length=10, choices=STATUS_CHOICES, default=EXPIRADO)
    changed_price = models.DecimalField("Preço em promoção", max_digits=10, decimal_places=2)
    original_price = models.DecimalField("Preço original", max_digits=10, decimal_places=2, blank=True,
                                         null=True)

    def clean(self):
        super().clean()

        # Ensure original price matches the product's current price
        if not self.original_price:
            self.original_price = self.product.price

        if self.original_price != self.product.price:
            raise ValidationError("Original price must match the product price.")

        # Ensure there is no overlap in the promotion time
        conflicting_promotions = Promotion.objects.filter(
            product=self.product,
            status__in=[self.ATIVO, self.PENDENTE],  # Check active or pending promotions
            starts_at__lt=self.expires_at,
            expires_at__gt=self.starts_at
        ).exclude(pk=self.pk)  # Exclude current promotion if updating

        if conflicting_promotions.exists():
            raise ValidationError("There is an overlapping promotion with this time period.")

        # Ensure only one promotion can be active at a time
        if self.status == self.ATIVO:
            active_promotion = Promotion.objects.filter(
                product=self.product,
                status=self.ATIVO
            ).exclude(pk=self.pk)

            if active_promotion.exists():
                raise ValidationError("There is already an active promotion for this product.")

    def save(self, *args, **kwargs):
        now = timezone.now()  # Get the current time

        # Update promotion status based on the current time
        if self.expires_at and now > self.expires_at:
            self.status = self.EXPIRADO
            if self.product.price != self.original_price:
                self.product.price = self.original_price  # Revert to original price if promotion expired
                self.product.save(update_fields=['price'])

        elif self.starts_at and now >= self.starts_at:
            self.status = self.ATIVO
            if self.product.price != self.changed_price:
                self.product.price = self.changed_price  # Apply promotion price
                self.product.save(update_fields=['price'])

        else:
            self.status = self.PENDENTE

        super().save(*args, **kwargs)  # Save the promotion instance

    def __str__(self):
        return f"Promoção do produto {self.product.name} - {self.status}"

    class Meta:
        ordering = ("-created",)
        verbose_name = "promoção"
        verbose_name_plural = "promoções"

        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['status']),
            models.Index(fields=['starts_at']),
        ]


class PromotionCode(TimeStampedModel):
    name = models.CharField('Nome', max_length=255, unique=True)
    description = models.TextField('Descrição', max_length=255, blank=True, null=True)

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
    role = models.ForeignKey(
        RoleType, verbose_name="Cargo", on_delete=models.CASCADE,
        related_name='promotion_codes', null=True, blank=True
    )
    can_with_promotion = models.BooleanField("Pode ser usado com outra promoção?", default=False)
    usable_in_roles = models.BooleanField("Pode ser usado em cargos?", default=False)
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

        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),

        ]

    def clean(self):
        super().clean()

        # Verifica se o código promocional está sendo aplicado a um cargo e se o produto está correto.
        if self.usable_in_roles:
            if not self.role:
                raise ValidationError("Um código de promoção para cargos deve ter um Role associado.")
            if self.product and not self.product.is_role:
                raise ValidationError("O produto associado não é um cargo, mas este código é para cargos.")
        else:
            if self.role:
                raise ValidationError("Códigos de promoção não aplicáveis a cargos não podem ter um Role associado.")

        # Verifica se o código é aplicável a uma categoria ou produto sem conflito.
        if self.product and self.category:
            raise ValidationError(
                "Um código de promoção deve ser aplicado a um produto ou a uma categoria, mas não a ambos.")

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
            user_code_usage = PromotionCodeUsage.objects.get_or_create(user=user, promotion_code=self)
            if user_code_usage.user_usage_count >= self.user_usage_limit:
                raise ValidationError(f"This promotion code has reached its usage limit for user {user.username}.")

        return True

    @transaction.atomic
    def apply_discount(self, product, category=None):
        """
        Apply the discount to a product. Returns the discounted price.
        """
        # Check if the product is a role and check if the code is applicable to the role
        if getattr(product, "is_role", False):
            if not self.usable_in_roles or (self.role and self.role != product.role_type):
                raise ValidationError("Este código não é aplicável ao cargo deste produto.")
        if not self.product and not self.category:
            raise ValidationError("This code is not applicable to any product or category.")
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

    @transaction.atomic
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
            promotion_code_usage = PromotionCodeUsage.objects.get_or_create(user=user, promotion_code=self)
            promotion_code_usage.user_usage_count += 1

    @transaction.atomic
    def restore_usage(self, user=None):
        """
        Restore the usage count of the promotion code.
        :param user: Who did use the code
        :return: None
        """
        # Decrement global usage count
        self.usage_count = F('usage_count') - 1
        self.save(update_fields=['usage_count'])

        if user:
            promotion_code_usage = PromotionCodeUsage.objects.get(user=user, promotion_code=self)
            if promotion_code_usage and promotion_code_usage.user_usage_count > 0:
                promotion_code_usage.user_usage_count = F('user_usage_count') - 1
                promotion_code_usage.save(update_fields=['user_usage_count'])


class PromotionCodeUsage(TimeStampedModel):
    """
    Tracks how many times a specific user has used a promotion code.
    """
    user = models.ForeignKey(User, verbose_name="Usuário", on_delete=models.PROTECT)
    promotion_code = models.ForeignKey(PromotionCode, verbose_name="Código Promocional", on_delete=models.PROTECT)
    user_usage_count = models.PositiveIntegerField("Contagem de uso por usuário", default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'promotion_code'], name='unique_payment_promotion_code')
        ]
        verbose_name = "Uso do Código Promocional"
        verbose_name_plural = "Usos de Códigos Promocionais"

        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['promotion_code']),
        ]

    def __str__(self):
        return f"{self.user} usou {self.promotion_code}"

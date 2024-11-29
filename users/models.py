from django.contrib.auth.models import AbstractUser, Permission
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from decimal import Decimal

from model_utils.models import TimeStampedModel, StatusModel

from datetime import timedelta, date

from users.managers import CachedUserManager, RoleManager, UserHistoryManager


class RoleType(TimeStampedModel):
    BRL, USD = 'BRL', 'USD'
    CURRENCY_CHOICES = (
        (BRL, 'Real (BRL)'),
        (USD, 'Dólar (USD)'),
    )

    name = models.CharField("Nome", max_length=50, unique=True)
    description = models.TextField("Descrição", blank=True)
    staff = models.BooleanField("Staff", default=False)
    price = models.DecimalField("Preço", max_digits=10, decimal_places=2)
    currency = models.CharField("Moeda", max_length=3, choices=CURRENCY_CHOICES, default=BRL)
    icon = models.CharField("Ícone", max_length=50)
    effective_days = models.DurationField("Dias de Vigência", default=timedelta(days=30))

    def __str__(self):
        return f"{self.name} - {self.get_currency_display()}"

    class Meta:
        ordering = ["-modified"]
        verbose_name = "tipo de cargo"
        verbose_name_plural = "tipos de cargo"


class Role(TimeStampedModel):
    expired = "expirado"
    active = "ativo"
    pending = "pendente"

    STATUS_CHOICES = [
        (expired, "Expirado"),
        (active, "Ativo"),
        (pending, "Pendente"),
    ]

    status = models.CharField("Status", max_length=10, choices=STATUS_CHOICES, default=pending)
    role_type = models.ForeignKey(RoleType, related_name="roles", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="roles", on_delete=models.CASCADE)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)

    objects = RoleManager()

    def save(self, *args, **kwargs):
        self.clean()

        # Set expiration date if not set yet
        if not self.expires_at and hasattr(self.role_type, 'effective_days'):
            self.expires_at = timezone.now() + self.role_type.effective_days

        self.verify_status()
        super().save(*args, **kwargs)

    def verify_status(self):
        # Determine status based on expiration
        self.status = self.expired if self.expires_at and timezone.now() >= self.expires_at else self.active

    def is_expired(self):
        # Use existing status verification to simplify expiration check
        return self.status == self.expired

    def __str__(self):
        return f"{self.user.username} - {self.role_type.name} ({self.get_status_display()})"

    class Meta:
        ordering = ["-modified"]
        verbose_name = "cargo"
        verbose_name_plural = "cargos"


def verify_birth_date(birth_date):
    if not birth_date:
        raise ValidationError("Usuário precisa ter uma data de nascimento válida.")
    else:
        today = date.today()
        age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        if age < 13:
            raise ValidationError("Você precisa ter 13 anos ou mais.")


class User(AbstractUser):
    balance = models.DecimalField(
        verbose_name="Saldo",
        default=0,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('999.99'))]
    )
    tos_accept = models.BooleanField("Aceita os Termos de Serviço", default=False)
    birth_date = models.DateField("Date de Nascimento", blank=True, null=True)

    objects = CachedUserManager()

    def clean(self):
        if not self.tos_accept:
            raise ValidationError("Usuário precisa aceitar os Termos de Serviço.")
        verify_birth_date(self.birth_date)

    def get_perfil_url(self):
        return reverse("pages:perfil", kwargs={"user_id": self.id})

    def get_update_url(self):
        return reverse("pages:update", kwargs={"user_id": self.id})

    def get_roles(self):
        # Fetch related roles, assuming a prefetching mechanism for optimization if necessary
        return self.roles.all() if hasattr(self, 'roles') else []

    def get_active_roles(self):
        # Helper to get only active, non-expired roles
        return [role for role in self.get_roles() if role.role_type and not role.is_expired()]

    def get_role_icon(self):
        active_roles = self.get_active_roles()
        return {role.role_type.id: role.role_type.icon for role in active_roles} if active_roles else ''

    def get_role_info(self):
        active_roles = self.get_active_roles()
        return {role.role_type.id: (f"Cargo: {role.role_type.name}"
                                    f"{', descrição: ' + role.role_type.description if
                                    role.role_type.description else ''}")
                for role in active_roles} if active_roles else ''

    def verify_pay_action(self, amount):
        """
        Check if the user has sufficient balance for the full amount.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        return self.balance >= amount

    def pay_with_balance(self, payment):
        """
        Deduct the amount from the user's balance if possible, and return a tuple indicating success and amount used.
        If balance is insufficient, use the entire balance.
        """
        # Lock the user's balance row for update
        amount, payment_id = Decimal(payment.amount), payment.id
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=self.pk)

                if user.verify_pay_action(amount):
                    # User can pay the entire amount
                    user.balance = Decimal(user.balance) - amount
                    user.save(update_fields=['balance'])
                    history = UserHistory(user_id=user.id,
                                          info=f'Saldo utilizado: {Decimal(amount)}, no pagamento #{payment_id}.',
                                          type=UserHistory.user_balance,
                                          link=reverse('payments:payment_detail',
                                                       kwargs={"payment_id": payment_id}))
                    return True, history
                else:
                    # User can pay only part of the amount
                    paid = Decimal(user.balance)
                    return False, paid
        except Exception as e:
            raise ValidationError(str(e))

    def refund_to_balance(self, payment):
        try:
            with transaction.atomic():
                payment_id, payment_amount = payment.id, payment.amount
                user = User.objects.select_for_update().get(pk=self.pk)
                user.balance += Decimal(payment_amount)
                user.save(update_fields=['balance'])
                history = UserHistory(user_id=user.id,
                                      info=f'Saldo reembolsado: {Decimal(payment_amount)}, do pagamento #{payment_id}.',
                                      type=UserHistory.user_balance_refund,
                                      link=reverse('payments:payment_detail',
                                                   kwargs={"payment_id": payment_id})
                                      )
                return history
        except Exception as e:
            raise ValidationError(str(e))

    class Meta:
        ordering = ['username']
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

        indexes = [
            models.Index(fields=['id'])
        ]


class UserHistory(TimeStampedModel):
    (user_balance,
     user_balance_refund,
     payment_create,
     payment_success,
     payment_fail) = ('user_balance',
                        'user_refund',
                        'payment_create',
                        'payment_success',
                        'payment_fail'
                      )
    type_choices = [
        (user_balance, 'Uso do saldo'),
        (user_balance_refund, 'Reembolso'),
        (payment_create, 'Pagamento criado'),
        (payment_success, 'Pagamento efetuado com sucesso'),
        (payment_fail, 'Pagamento falhou'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Usuário', on_delete=models.CASCADE)
    type = models.CharField(verbose_name='Tipo', max_length=50, choices=type_choices, default=user_balance)
    info = models.TextField(verbose_name='Informação', max_length=500, blank=True, null=True)
    link = models.TextField(verbose_name='Link', max_length=500, blank=True, null=True)

    objects = UserHistoryManager()

    class Meta:
        ordering = ['user']
        verbose_name = "histórico"
        verbose_name_plural = "históricos"

    def __str__(self):
        return f'Histórico do usuário {self.user}'

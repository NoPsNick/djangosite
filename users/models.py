from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError

from model_utils.models import TimeStampedModel, StatusModel
# from localflavor.br.models import BRPostalCodeField, BRStateField

from datetime import timedelta, date

from users.managers import CachedUserManager


# class Address(TimeStampedModel):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="addresses", on_delete=models.CASCADE)
#     postal_code = BRPostalCodeField("CEP")
#     rua = models.CharField("Rua", max_length=250)
#     number = models.CharField("Número", max_length=250)
#     complement = models.CharField("Complemento", max_length=250, blank=True)
#     district = models.CharField("Bairro", max_length=250)
#     state = BRStateField("Estado")
#     city = models.CharField("Cidade", max_length=250)
#     selected = models.BooleanField("Selecionado", default=False)
#
#     objects = AddressManager()
#
#     def get_absolute_url(self):
#         return reverse("pages:address_update", kwargs={"pk": self.id}) if not self.selected else reverse(
#             'pages:address_list')
#
#     def get_remove_url(self):
#         return reverse("pages:address_delete", kwargs={"pk": self.id}) if not self.selected else reverse(
#             'pages:address_list')
#
#     def get_full_address(self):
#         complemento = f"\nComplemento: {self.complement}" if self.complement else ""
#         return (f"Endereço: {self.rua}, {self.number}, {self.postal_code}\n"
#                 f"Bairro: {self.district}\n"
#                 f"Cidade: {self.city}\n"
#                 f"Estado: {self.state}{complemento}")
#
#     def set_address_as_selected(self):
#         # Desmarca o endereço atualmente selecionado
#         Address.objects.filter(user=self.user, selected=True).update(selected=False)
#         self.selected = True
#         self.save()
#         self.user.address = self
#         self.user.save()
#
#     def __str__(self):
#         return f"{self.postal_code} {self.id}"
#
#     def get_address_info(self):
#         return f"{self.postal_code} {self.id}"
#
#     class Meta:
#         constraints = [
#             # Ensures only one address can be selected per user
#             models.UniqueConstraint(fields=['user'], condition=models.Q(selected=True),
#                                     name='unique_selected_address_per_user')
#         ]
#         verbose_name = "endereço"
#         verbose_name_plural = "endereços"


# class PhoneNumber(TimeStampedModel):
#
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="phones", on_delete=models.CASCADE)
#     number = models.CharField("Número do telefone", max_length=30)
#     selected = models.BooleanField("Selecionado", default=False)
#
#     objects = PhoneNumberManager()
#
#     def get_absolute_url(self):
#         return reverse("pages:phone_update", kwargs={"pk": self.id}) if not self.selected else reverse(
#             'pages:phone_list')
#
#     def get_remove_url(self):
#         return reverse("pages:phone_delete", kwargs={"pk": self.id}) if not self.selected else reverse(
#             'pages:phone_list')
#
#     def set_phone_number_as_selected(self):
#         # Desmarca o telefone atualmente selecionado
#         PhoneNumber.objects.filter(user=self.user, selected=True).update(selected=False)
#         self.selected = True
#         self.save()
#         self.user.phone_number = self
#         self.user.save()
#
#     def __str__(self):
#         return f'{self.number}'
#
#     def get_phone_info(self):
#         return f'{self.number}'
#
#     class Meta:
#         constraints = [
#             # Ensures only one phone number can be selected per user
#             models.UniqueConstraint(fields=['user'], condition=models.Q(selected=True), name='unique_selected_phone_per_user')
#         ]
#         verbose_name = "telefone"
#         verbose_name_plural = "telefones"


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
    permissions = models.ManyToManyField('auth.Permission', blank=True, related_name="role_perms")

    def __str__(self):
        return f"{self.name} - {self.get_currency_display()}"

    class Meta:
        ordering = ["-modified"]
        verbose_name = "tipo de cargo"
        verbose_name_plural = "tipos de cargo"


class Role(StatusModel, TimeStampedModel):
    EXPIRADO = "Expirado"
    ATIVO = "Ativo"
    PENDENTE = "Pendente"

    STATUS_CHOICES = [
        (EXPIRADO, "Expirado"),
        (ATIVO, "Ativo"),
        (PENDENTE, "Pendente"),
    ]

    status = models.CharField("Status", max_length=10, choices=STATUS_CHOICES, default=PENDENTE)
    role_type = models.ForeignKey(RoleType, related_name="roles", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="roles", on_delete=models.CASCADE)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def save(self, *args, **kwargs):
        self.clean()
        # Set expiration date if not set yet
        if not self.expires_at:
            self.expires_at = timezone.now() + self.role_type.effective_days

        # Automatically update the status
        self.verify_status()

        super().save(*args, **kwargs)

    def verify_status(self):
        # Check if the role is expired or active
        if self.expires_at and timezone.now() >= self.expires_at:
            self.status = self.EXPIRADO
        else:
            self.status = self.ATIVO

    def is_expired(self):
        # Explicit check if the role is expired
        return timezone.now() >= self.expires_at

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

    role = models.OneToOneField(Role, verbose_name="Cargo", related_name="role", default=None, null=True, blank=True,
                                on_delete=models.SET_NULL)
    balance = models.PositiveIntegerField("Saldo", default=0)
    # address = models.OneToOneField(Address, verbose_name="Endereço", related_name="user_from_address",
    #                                on_delete=models.SET_NULL, null=True, blank=True)
    # phone_number = models.OneToOneField(PhoneNumber, verbose_name="Telefone", related_name="user_from_phone",
    #                                     on_delete=models.SET_NULL, null=True, blank=True)
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

    def get_role_icon(self):
        if self.role and self.role.role_type and not self.role.is_expired():
            return self.role.role_type.icon
        return ''

    # def verify_address(self):
    #     addresses = Address.objects.get_user_addresses(self)
    #     if addresses:
    #         num_addresses = len(addresses)
    #         return num_addresses < getattr(settings, 'MAX_ADDRESS_PER_USER', 2)
    #     return True
    #
    # def verify_phone_number(self):
    #     phone_numbers = PhoneNumber.objects.get_user_phone_numbers(self)
    #     if phone_numbers:
    #         num_phone_numbers = len(phone_numbers)
    #         return num_phone_numbers < getattr(settings, 'MAX_PHONE_NUMBER_PER_USER', 2)
    #     return True

    class Meta:
        ordering = ['username']
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['username']),
        ]

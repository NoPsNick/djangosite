from django.contrib.auth import get_user_model
from django.db import models
from model_utils.models import TimeStampedModel

from .managers import TermOfServiceManager

User = get_user_model()


# Create your models here.
class Contract(TimeStampedModel):
    title = models.CharField("Título", max_length=200)
    description = models.TextField("Descrição")
    file = models.FileField("Contrato", upload_to='docs/contracts/')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "contrato"
        verbose_name_plural = "contratos"


class PrivacyPolicy(TimeStampedModel):
    title = models.CharField("Título", max_length=200)
    content = models.TextField("Conteúdo")
    effective_date = models.DurationField(verbose_name="Data de Vigência")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "politica de privacidade"
        verbose_name_plural = "politicas de privacidade"


class ReturnPolicy(TimeStampedModel):
    title = models.CharField("Título", max_length=200)
    content = models.TextField("Conteúdo")
    effective_date = models.DurationField(verbose_name="Data de Vigência")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "politica de retorno"
        verbose_name_plural = "politicas de retorno"


class TermOfService(TimeStampedModel):
    title = models.CharField('Título', max_length=200)
    content = models.TextField('Conteúdo')
    who_made = models.OneToOneField(User, on_delete=models.CASCADE)

    objects = TermOfServiceManager()

    def __str__(self):
        return f'{self.title} feito por: {self.who_made}'

    class Meta:
        verbose_name = "termo de serviço"
        verbose_name_plural = "termos de serviço"
from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel
from django.core.cache import caches

from .managers import TermOfServiceManager, PrivacyPolicyManager, ReturnPolicyManager



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

    objects = PrivacyPolicyManager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "politica de privacidade"
        verbose_name_plural = "politicas de privacidade"


class ReturnPolicy(TimeStampedModel):
    title = models.CharField("Título", max_length=200)
    content = models.TextField("Conteúdo")
    effective_date = models.DurationField(verbose_name="Data de Vigência")

    objects = ReturnPolicyManager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "politica de devolução"
        verbose_name_plural = "politicas de devolução"


class TermOfService(TimeStampedModel):
    title = models.CharField('Título', max_length=200)
    content = models.TextField('Conteúdo')

    objects = TermOfServiceManager()

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = "termo de serviço"
        verbose_name_plural = "termos de serviço"

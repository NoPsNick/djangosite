from django.db import models
from model_utils.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.core.cache import cache


class About(TimeStampedModel):
    position = models.IntegerField(
        "Posição",
        unique=True,
        db_index=True,
        help_text="(Obrigatório, não podendo ser igual a nenhum outro) Posição em que o conteúdo ficará, começando do "
                  "menor (parte superior da página) para o maior (parte inferior da página).",
    )
    image_cima = models.ImageField(
        "Imagem de cima",
        upload_to="about/cima/%Y/%m/%d",
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        help_text="Imagem que caso tiver, aparecerá em cima do título.",
    )
    link_image_cima = models.URLField(
        "Link da imagem de cima",
        blank=True,
        max_length=255,
        help_text="Link da imagem de cima. Caso tiver, ao clicar na imagem será redirecionado para o local colocado.",
    )
    image_meio = models.ImageField(
        "Imagem no meio",
        upload_to="about/meio/%Y/%m/%d",
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        help_text="Imagem que caso tiver, aparecerá abaixo do título, entre a descrição e o título.",
    )
    link_image_meio = models.URLField(
        "Link da imagem do meio",
        blank=True,
        max_length=255,
        help_text="Link da imagem do meio. Caso tiver, ao clicar na imagem será redirecionado para o local colocado.",
    )
    image_baixo = models.ImageField(
        "Imagem de baixo",
        upload_to="about/baixo/%Y/%m/%d",
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        help_text="Imagem que caso tiver, aparecerá abaixo da descrição.",
    )
    link_image_baixo = models.URLField(
        "Link da imagem de baixo",
        blank=True,
        max_length=255,
        help_text="Link de baixo. Caso tiver, ao clicar na imagem será redirecionado para o local colocado.",
    )
    title = models.CharField("Título", blank=True, max_length=255)
    link_title = models.URLField(
        "Link do título",
        blank=True,
        max_length=255,
        help_text="Link do título. Caso tiver, ao clicar no título será redirecionado para o local colocado.",
    )
    description = models.TextField("Descrição", blank=True)
    link_description = models.URLField(
        "Link da descrição",
        blank=True,
        max_length=255,
        help_text="Link da descrição. Caso tiver, ao clicar no texto padrão: 'Clique Aqui', será redirecionado para o "
                  "local colocado.",
    )
    text_link_description = models.CharField(
        "Texto para clicar",
        blank=True,
        max_length=255,
        default="Clique Aqui",
        help_text="Texto em que ao clicar será redirecionado ao local dito no link da descrição. Padrão: 'Clique Aqui'.",
    )
    last = models.BooleanField(
        "Último da linha?",
        default=False,
        help_text="Adiciona uma quebra no final, para que os próximos sejam em baixo.",
    )

    class Meta:
        ordering = ("position", "created")
        verbose_name = "Sobre"
        verbose_name_plural = "Sobre"

    def __str__(self):
        return self.title or f"Conteúdo na posição {self.position}"

    def clean(self):
        if About.objects.exclude(id=self.id).filter(position=self.position).exists():
            raise ValidationError(f"A posição {self.position} já está em uso por outro conteúdo.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('about_list')  # Invalida o cache ao salvar

    def delete(self, *args, **kwargs):
        cache.delete('about_list')  # Invalida o cache ao deletar
        super().delete(*args, **kwargs)

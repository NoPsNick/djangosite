from django.db import models


class EstoqueManager(models.Manager):

    def get_product(self, produto_id):
        try:
            return self.get(produto_id=produto_id)
        except self.model.DoesNotExist:
            return None


class AvailableManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)

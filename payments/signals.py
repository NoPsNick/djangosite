from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Payment
from .services import payments_cache_key_builder


@receiver(post_save, sender=Payment)
@receiver(post_delete, sender=Payment)
def product_post_save(sender, instance, **kwargs):
    cache_key = payments_cache_key_builder(instance.customer.id)
    cache.delete(cache_key)
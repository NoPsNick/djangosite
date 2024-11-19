from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Order
from .services import orders_cache_key_builder


@receiver(post_save, sender=Order)
@receiver(post_delete, sender=Order)
def order_post_change(sender, instance, **kwargs):
    cache_key = orders_cache_key_builder(instance.customer.id)
    cache.delete(cache_key)

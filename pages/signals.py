from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import caches

from .models import About


@receiver(post_save, sender=About)
@receiver(post_delete, sender=About)
def update_about_cache(sender, instance, **kwargs):
    cache_key = 'about_list'
    file_cache = caches['file_based']
    file_cache.delete(cache_key)
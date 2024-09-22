from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache, caches

from users.models import Address, PhoneNumber
from .models import About


# Address Cache Invalidation
@receiver(post_save, sender=Address)
def update_address_cache(sender, instance, **kwargs):
    """
    Update Address cache when an Address is created or updated.
    """
    cache_key = f'user_{instance.user.id}_addresses'
    cache.delete(cache_key)  # Delete the actually addresses

@receiver(post_delete, sender=Address)
def delete_address_cache(sender, instance, **kwargs):
    """
    Remove Address from cache and update the Address list when a Address is deleted.
    """
    cache_key = f'user_{instance.user.id}_addresses'
    cache.delete(cache_key)  # Remove addresses from cache

# Category Cache Invalidation
@receiver(post_save, sender=PhoneNumber)
def update_category_cache(sender, instance, **kwargs):
    """
    Update PhoneNumber cache when a PhoneNumber is created or updated.
    """
    cache_key = f'user_{instance.user.id}_phone_numbers'
    cache.delete(cache_key) # Delete the actually phonenumbers

@receiver(post_delete, sender=PhoneNumber)
def delete_category_cache(sender, instance, **kwargs):
    """
    Remove PhoneNumber from cache when a PhoneNumber is deleted.
    """
    cache_key = f'user_{instance.user.id}_phone_numbers'
    cache.delete(cache_key)  # Delete the actually phonenumbers


@receiver(post_save, sender=About)
def update_about_cache(sender, instance, **kwargs):
    cache_key = 'about_list'
    file_cache = caches['file_based']
    file_cache.delete(cache_key)


@receiver(post_delete, sender=About)
def update_about_cache(sender, instance, **kwargs):
    cache_key = 'about_list'
    file_cache = caches['file_based']
    file_cache.delete(cache_key)
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache

from allauth.account.signals import (user_logged_in, user_signed_up, user_logged_out,
                                     password_set, password_reset, password_changed,
                                     email_changed, email_added, email_confirmed, email_removed)

from .managers import CachedUserManager
from .models import Role

User = get_user_model()


@receiver(post_save, sender=Role)
def add_vip_permissions(sender, instance, **kwargs):
    instance.verify_status()
    instance.save()
    vip_type = instance.role_type
    if vip_type:
        for perm in vip_type.permissions.all():
            instance.user.user_permissions.add(perm)
        instance.user.save()


@receiver(post_delete, sender=Role)
def remove_vip_permissions(sender, instance, **kwargs):
    vip_type = instance.role_type
    if vip_type:
        for perm in vip_type.permissions.all():
            instance.user.user_permissions.remove(perm)
        instance.user.save()


@receiver(post_save, sender=User)
def update_cached_user(sender, instance, **kwargs):
    cache_key = f'user_auth_{instance.pk}'
    cache.set(cache_key, instance, timeout=3600)  # Update the cache when user is saved


@receiver(post_delete, sender=User)
def remove_cached_user(sender, instance, **kwargs):
    cache_key = f'user_auth_{instance.pk}'
    cache.delete(cache_key)


@receiver(user_logged_in)
@receiver(user_signed_up)
@receiver(password_reset)
@receiver(password_changed)
@receiver(password_set)
@receiver(email_confirmed)
@receiver(email_removed)
@receiver(email_changed)
@receiver(email_added)
def cache_user_on_sign_in(sender, request, user, **kwargs):
    cache_key = CachedUserManager().get_cache_key(user.id)
    cache.set(cache_key, user, CachedUserManager().CACHE_TIMEOUT)


@receiver(user_logged_out)
def clear_user_cache_on_logout(sender, request, user, **kwargs):
    cache_key = CachedUserManager().get_cache_key(user.id)
    cache.delete(cache_key)
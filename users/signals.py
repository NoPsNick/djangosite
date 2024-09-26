from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.auth import get_user_model
from django.conf import settings

from allauth.account.signals import (
    user_logged_in, user_logged_out, user_signed_up,
    password_reset, password_changed, password_set,
    email_confirmed, email_removed, email_changed, email_added
)

from pages.serializers import UserSerializer  # Assuming you have a serializer for the User
from users.models import Role

User = get_user_model()

CACHE_TIMEOUT = settings.CACHE_TIMEOUT or 60 * 15  # Define your cache timeout centrally

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


def get_cache_key(user_id):
    """Helper function to generate consistent cache keys."""
    return f'user_{user_id}_profile'


@receiver(post_save, sender=User)
def update_cached_user(sender, instance, **kwargs):
    """Update the cached user data when a user instance is saved."""
    cache_key = get_cache_key(instance.pk)
    serializer = UserSerializer(instance)  # Serialize the user data
    cache.set(cache_key, serializer.data, timeout=CACHE_TIMEOUT)  # Cache the serialized data


@receiver(post_delete, sender=User)
def remove_cached_user(sender, instance, **kwargs):
    """Remove the user from cache when the user is deleted."""
    cache_key = get_cache_key(instance.pk)
    cache.delete(cache_key)


# Caching user data on login, sign-up, password, or email changes
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
    """Cache the user data when logged in, signed up, or user information is changed."""
    cache_key = get_cache_key(user.id)
    serializer = UserSerializer(user)  # Serialize the user data
    cache.set(cache_key, serializer.data, timeout=CACHE_TIMEOUT)  # Cache the serialized data


@receiver(user_logged_out)
def clear_user_cache_on_logout(sender, request, user, **kwargs):
    """Clear the user cache on logout."""
    cache_key = get_cache_key(user.id)
    cache.delete(cache_key)

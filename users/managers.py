from django.db import models
from django.contrib.auth.models import UserManager
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.conf import settings


class PhoneNumberManager(models.Manager):
    def get_selected_phone_number(self, user):
        phone_numbers = self.get_user_phone_numbers(user)
        if phone_numbers:
            return next((number for number in phone_numbers if number['selected']), None)
        return None

    def get_user_phone_numbers(self, user):
        from pages.serializers import PhoneNumberSerializer
        cache_key = f"user_{user.id}_phone_numbers"
        phone_numbers = cache.get(cache_key)

        if phone_numbers is None:
            # Only fetch phone_numbers belonging to the specified user
            phone_numbers_queryset = self.filter(user=user).order_by('selected', 'created')
            if phone_numbers_queryset.exists():
                sorted_numbers = sorted(
                    phone_numbers_queryset,
                    key=lambda x: (-x.selected, -x.created.timestamp() if x.created else 0)
                )
                serializer = PhoneNumberSerializer(sorted_numbers, many=True)
                phone_numbers = serializer.data
                cache.set(cache_key, phone_numbers, timeout=settings.CACHE_TIMEOUT)

        return phone_numbers



class AddressManager(models.Manager):
    def get_selected_address(self, user):
        addresses = self.get_user_addresses(user)
        if addresses:
            return next((address for address in addresses if address['selected']), None)
        return None

    def get_user_addresses(self, user):
        from pages.serializers import AddressSerializer
        cache_key = f"user_{user.id}_addresses"
        addresses = cache.get(cache_key)

        if addresses is None:
            # Only fetch addresses belonging to the specified user
            addresses_queryset = self.filter(user=user).order_by('selected', 'created')
            if addresses_queryset.exists():
                sorted_addresses = sorted(
                    addresses_queryset,
                    key=lambda x: (-x.selected, -x.created.timestamp() if x.created else 0)
                )
                serializer = AddressSerializer(sorted_addresses, many=True)
                addresses = serializer.data
                cache.set(cache_key, addresses, timeout=settings.CACHE_TIMEOUT)

        return addresses


class CachedUserManager(UserManager):
    CACHE_KEY_PREFIX = 'user_'
    CACHE_TIMEOUT = 60 * 15  # 15 minutes

    def get_cache_key(self, user_id):
        return f"{self.CACHE_KEY_PREFIX}{user_id}"

    def get(self, *args, **kwargs):
        user_id = kwargs.get('id')
        cache_key = self.get_cache_key(user_id)

        user = cache.get(cache_key)
        if not user:
            user = super().get(*args, **kwargs)
            if not user.is_active:
                raise PermissionDenied("User account is disabled")
            cache.set(cache_key, user, self.CACHE_TIMEOUT)
        return user

    def update(self, user, *args, **kwargs):
        super().update(user, *args, **kwargs)
        cache_key = self.get_cache_key(user.id)
        cache.set(cache_key, user, self.CACHE_TIMEOUT)
        return user

    def delete(self, *args, **kwargs):
        user = self.get(*args, **kwargs)
        cache_key = self.get_cache_key(user.id)
        super().delete(*args, **kwargs)
        cache.delete(cache_key)

from django.contrib.auth.models import UserManager
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import models
from django.conf import settings



class CachedUserManager(UserManager):
    CACHE_TIMEOUT = 60 * 60 * 2  # 2 hours

    @staticmethod
    def get_cache_key(user_id):
        return f"user_{user_id}_auth"

    def get(self, *args, **kwargs):
        user_id = kwargs.get('pk')
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


class UserHistoryManager(models.Manager):
    @staticmethod
    def get_history_cache_key(user_id):
        return f"user_{user_id}_histories"

    def get_cached_histories(self, user_id):
        cache_key = self.get_history_cache_key(user_id)
        cached_histories = cache.get(cache_key)

        if cached_histories is None:
            cached_histories = self._get_all_histories(user_id)

        return cached_histories

    def update_historic(self, user_id, historic):
        from .serializers import UserHistorySerializer
        histories = self.get_cached_histories(user_id)
        histories[historic.id] = UserHistorySerializer(historic).data
        cache_key = self.get_history_cache_key(user_id)
        cached_histories = histories
        cache.set(cache_key, cached_histories, getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7))

    def delete_historic(self, user_id, historic):
        histories = self.get_cached_histories(user_id) or {}
        histories.pop(historic.id, None)
        cache_key = self.get_history_cache_key(user_id)
        cached_histories = histories
        cache.set(cache_key, cached_histories, getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7))

    def _get_all_histories(self, user_id):
        from .serializers import UserHistorySerializer
        cache_key = self.get_history_cache_key(user_id)
        user_history_queryset = self.filter(user=user_id)
        cached_histories = {}

        for history in user_history_queryset:
            history_data = UserHistorySerializer(history).data
            cached_histories[history.id] = history_data

        cache.set(cache_key, cached_histories, getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7))
        return cached_histories


class RoleManager(models.Manager):

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related('role_type', 'user')

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

    @staticmethod
    def _serialize_history(historic):
        from .serializers import UserHistorySerializer
        return UserHistorySerializer(historic).data

    def get_cached_histories(self, user_id):
        cache_key = self.get_history_cache_key(user_id)
        return cache.get_or_set(cache_key, lambda: self._get_all_histories(user_id))

    def update_historic(self, user_id, historic):
        histories = self.get_cached_histories(user_id)
        histories[historic.id] = self._serialize_history(historic)
        self._set_cache(user_id, histories)

    def delete_historic(self, user_id, historic):
        histories = self.get_cached_histories(user_id)
        histories.pop(historic.id, None)
        self._set_cache(user_id, histories)

    def _get_all_histories(self, user_id):
        histories = {
            history.id: self._serialize_history(history)
            for history in self.filter(user=user_id)
        }
        self._set_cache(user_id, histories)
        return histories

    def _set_cache(self, user_id, histories):
        cache.set(self.get_history_cache_key(user_id), histories, getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7))


class RoleManager(models.Manager):

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related('role_type', 'user')

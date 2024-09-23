from django.conf import settings
from django.db import models
from django.core.cache import caches


class TermOfServiceManager(models.Manager):
    def get_terms_of_service(self):
        from .serializers import TermOfServiceSerializer
        file_cache = caches['file_based']
        tos = file_cache.get(settings.CACHE_KEY_TERMS_OF_SERVICE)

        if tos is None:
            get_tos = self.order_by('modified', 'created')
            if get_tos.exists():
                serializer = TermOfServiceSerializer(get_tos, many=True)
                tos = serializer.data
            file_cache.set(settings.CACHE_KEY_TERMS_OF_SERVICE, tos,
                           timeout=settings.HIGH_TIME_CACHE_TIMEOUT or 60 * 60 * 24 * 30)

        return tos


class PrivacyPolicyManager(models.Manager):
    def get_privacy_policies(self):
        from .serializers import PrivacyPolicySerializer
        file_cache = caches['file_based']
        privacy_policy = file_cache.get(settings.CACHE_KEY_PRIVACY_POLICY)

        if privacy_policy is None:
            get_privacy_policy = self.order_by('modified', 'created')
            if get_privacy_policy.exists():
                serializer = PrivacyPolicySerializer(get_privacy_policy, many=True)
                privacy_policy = serializer.data
            file_cache.set(settings.CACHE_KEY_PRIVACY_POLICY, privacy_policy,
                           timeout=settings.HIGH_TIME_CACHE_TIMEOUT or 60 * 60 * 24 * 30)

        return privacy_policy


class ReturnPolicyManager(models.Manager):
    def get_return_policies(self):
        from .serializers import ReturnPolicySerializer
        file_cache = caches['file_based']
        return_policy = file_cache.get(settings.CACHE_KEY_RETURN_POLICY)

        if return_policy is None:
            get_return_policy = self.order_by('modified', 'created')
            if get_return_policy.exists():
                serializer = ReturnPolicySerializer(get_return_policy, many=True)
                return_policy = serializer.data
            file_cache.set(settings.CACHE_KEY_RETURN_POLICY, return_policy,
                           timeout=settings.HIGH_TIME_CACHE_TIMEOUT or 60 * 60 * 24 * 100)

        return return_policy

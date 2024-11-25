from django.conf import settings
from django.db import models

from .services import get_cached_data


class TermOfServiceManager(models.Manager):
    def get_terms_of_service(self):
        from .serializers import TermOfServiceSerializer
        return get_cached_data(self, settings.CACHE_KEY_TERMS_OF_SERVICE,
                               TermOfServiceSerializer, settings.HIGH_TIME_CACHE_TIMEOUT or 60 * 60 * 24 * 100)


class PrivacyPolicyManager(models.Manager):
    def get_privacy_policies(self):
        from .serializers import PrivacyPolicySerializer
        return get_cached_data(self, settings.CACHE_KEY_PRIVACY_POLICY,
                               PrivacyPolicySerializer, settings.HIGH_TIME_CACHE_TIMEOUT or 60 * 60 * 24 * 100)


class ReturnPolicyManager(models.Manager):
    def get_return_policies(self):
        from .serializers import ReturnPolicySerializer
        return get_cached_data(self, settings.CACHE_KEY_RETURN_POLICY,
                               ReturnPolicySerializer, settings.HIGH_TIME_CACHE_TIMEOUT or 60 * 60 * 24 * 100)

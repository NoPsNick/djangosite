from django.conf import settings
from django.db import models
from django.core.cache import caches


CACHE_KEY = 'tos'

class TermOfServiceManager(models.Manager):
    def get_terms_of_services(self):
        from .serializers import TermOfServiceSerializer
        file_cache = caches['file_based']
        tos = file_cache.get(CACHE_KEY)

        if tos is None:
            get_tos = self.order_by('modified', 'created')
            if get_tos.exists():
                serializer = TermOfServiceSerializer(get_tos, many=True)
                tos = serializer.data
            file_cache.set(CACHE_KEY, tos, timeout=settings.CACHE_TIMEOUT or 60 * 60 * 24 * 30)

        return tos
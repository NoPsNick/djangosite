from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import caches
from django.conf import settings

from .models import ReturnPolicy, TermOfService, PrivacyPolicy


@receiver(post_save, sender=ReturnPolicy)
@receiver(post_delete, sender=ReturnPolicy)
def post_save_return_policy(sender, instance, **kwargs):
    file_cache = caches['file_based']
    return_policies = file_cache.get(settings.CACHE_KEY_RETURN_POLICY)
    return_policies.clear()
    sender.objects.get_return_policies()


@receiver(post_save, sender=PrivacyPolicy)
@receiver(post_delete, sender=PrivacyPolicy)
def post_save_privacy_policy(sender, instance, **kwargs):
    file_cache = caches['file_based']
    privacy_policies = file_cache.get(settings.CACHE_KEY_PRIVACY_POLICY)
    privacy_policies.clear()
    sender.objects.get_privacy_policies()


@receiver(post_save, sender=TermOfService)
@receiver(post_delete, sender=TermOfService)
def post_save_term_of_service(sender, instance, **kwargs):
    file_cache = caches['file_based']
    terms_of_service = file_cache.get(settings.CACHE_KEY_TERMS_OF_SERVICE)
    terms_of_service.clear()
    sender.objects.get_terms_of_service()

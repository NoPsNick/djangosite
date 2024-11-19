from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Payment, PaymentStatus
from .services import payments_cache_key_builder, PaymentService


@receiver(post_delete, sender=Payment)
@receiver(post_save, sender=Payment)
def payment_change(sender, instance, **kwargs):
    cache_key = payments_cache_key_builder(instance.customer.id)
    cache.delete(cache_key)


@receiver(pre_delete, sender=Payment)
def payment_pre_delete(sender, instance, **kwargs):
    try:
        if instance.status == PaymentStatus.PENDING or instance.status == PaymentStatus.COMPLETED:
            with transaction.atomic():
                PaymentService(instance).process_payment_status()
    except ValidationError:
        pass

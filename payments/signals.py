from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from .models import Payment, PaymentStatus
from .services import PaymentService


@receiver(post_save, sender=Payment)
def update_payment_cache(sender, instance, **kwargs):
    """
    Update the cache when a Payment is created or updated.
    """
    Payment.objects.update_cached_payment(instance)


@receiver(post_delete, sender=Payment)
def delete_payment_cache(sender, instance, **kwargs):
    """
    Remove the Payment from cache when deleted.
    """
    Payment.objects.delete_cached_payment(instance)


@receiver(pre_delete, sender=Payment)
def payment_pre_delete(sender, instance, **kwargs):
    try:
        if instance.status == PaymentStatus.PENDING or instance.status == PaymentStatus.COMPLETED:
            payment_service = PaymentService(instance)
            payment_service.process_payment_status(_save=False)
            payment_service.bulk_create_histories()
    except ValidationError:
        pass

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Order


@receiver(post_save, sender=Order)
def order_post_change(sender, instance, **kwargs):
    sender.objects.update_cached_orders(instance)


@receiver(post_delete, sender=Order)
def order_post_delete(sender, instance, **kwargs):
    sender.objects.delete_cached_order(instance)

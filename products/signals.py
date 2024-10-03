from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Product, Category, Promotion, Stock
from .services import update_product_cache, delete_product_cache, update_category_cache, delete_category_cache
from pages.services import update_promotion_cache, remove_promotion_cache


# Register signals for Product
@receiver(post_save, sender=Product)
def product_post_save(sender, instance, **kwargs):
    update_product_cache(sender, instance)


@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    delete_product_cache(sender, instance)


@receiver(post_save, sender=Stock)
def stock_post_save(sender, instance, **kwargs):
    update_product_cache(sender, instance.product)


@receiver(post_delete, sender=Stock)
def stock_post_delete(sender, instance, **kwargs):
    delete_product_cache(sender, instance.product)


# Register signals for Category
@receiver(post_save, sender=Category)
def category_post_save(sender, instance, **kwargs):
    update_category_cache(sender, instance)


@receiver(post_delete, sender=Category)
def category_post_delete(sender, instance, **kwargs):
    delete_category_cache(sender, instance)


@receiver(post_save, sender=Promotion)
def update_promotion_post_save(sender, instance, **kwargs):
    # Update the cache when a promotion is added/updated
    update_promotion_cache(instance)


@receiver(post_delete, sender=Promotion)
def revert_price_on_promotion_delete(sender, instance, **kwargs):
    # Revert the product's price when a promotion is deleted
    if instance.product and instance.original_price:
        instance.product.price = instance.original_price
        instance.product.save(update_fields=['price'])

    # Remove the promotion from the cache
    remove_promotion_cache(instance)

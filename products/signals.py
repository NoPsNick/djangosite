from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
import logging

from .models import Product, Category, Promotion, Stock
from .services import (
    update_product_cache,
    delete_product_cache,
    update_category_cache,
    delete_category_cache,
)
from pages.services import update_promotion_cache, remove_promotion_cache

logger = logging.getLogger('celery')


# Função genérica para manipular cache de produtos
def safe_update_product_cache(product):
    try:
        update_product_cache(Product, product)
    except Exception as e:
        logger.error(f"Failed to update product cache for {product.slug}: {e}")


def safe_delete_product_cache(product):
    try:
        delete_product_cache(Product, product)
    except Exception as e:
        logger.error(f"Failed to delete product cache for {product.slug}: {e}")


# Register signals for Product
@receiver(post_save, sender=Product)
def product_post_save(sender, instance, **kwargs):
    safe_update_product_cache(instance)


@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    safe_delete_product_cache(instance)


# Register signals for Stock
@receiver(post_save, sender=Stock)
def stock_post_save(sender, instance, **kwargs):
    safe_update_product_cache(instance.product)


@receiver(post_delete, sender=Stock)
def stock_post_delete(sender, instance, **kwargs):
    safe_delete_product_cache(instance.product)


# Register signals for Category
@receiver(post_save, sender=Category)
def category_post_save(sender, instance, **kwargs):
    try:
        update_category_cache(Category, instance)
    except Exception as e:
        logger.error(f"Failed to update category cache for {instance.slug}: {e}")


@receiver(post_delete, sender=Category)
def category_post_delete(sender, instance, **kwargs):
    try:
        delete_category_cache(Category, instance)
    except Exception as e:
        logger.error(f"Failed to delete category cache for {instance.slug}: {e}")


# Register signals for Promotion
@receiver(post_save, sender=Promotion)
def promotion_post_save(sender, instance, **kwargs):
    try:
        update_promotion_cache(instance)
    except Exception as e:
        logger.error(f"Failed to update promotion cache for {instance.id}: {e}")


@receiver(post_delete, sender=Promotion)
def promotion_post_delete(sender, instance, **kwargs):
    try:
        # Revert the product's price
        Product.objects.update_promotion_product_price(instance.product.slug, instance.original_price)

        # Remove promotion cache
        remove_promotion_cache(instance)
    except ObjectDoesNotExist:
        logger.warning(f"Product for promotion {instance.id} does not exist.")
    except Exception as e:
        logger.error(f"Error while handling promotion deletion for {instance.id}: {e}")

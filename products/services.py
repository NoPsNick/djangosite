from django.conf import settings
from django.core.cache import cache

from .serializers import ProductSerializer, CategorySerializer
from .models import Category, Product

PRODUCT_SLUGS_KEY = 'product_slugs'
CATEGORY_SLUGS_KEY = 'category_slugs'


def get_product_from_cache(slug):
    cache_key = f'product_{slug}'
    product_data = cache.get(cache_key)

    if not product_data:
        # If not cached, retrieve from DB and cache it
        try:
            product = Product.objects.get(slug=slug)
            product_data = ProductSerializer(product).data
            cache.set(cache_key, product_data, timeout=settings.CACHE_TIMEOUT)
        except Product.DoesNotExist:
            return None
    return product_data


def get_category_from_cache(slug):
    cache_key = f'category_{slug}'
    category_data = cache.get(cache_key)

    if not category_data:
        # If not cached, retrieve from DB and cache it
        try:
            category = Category.objects.get(slug=slug)
            category_data = CategorySerializer(category).data
            cache.set(cache_key, category_data, timeout=settings.CACHE_TIMEOUT)
        except Category.DoesNotExist:
            return None
    return category_data


def cache_product_list(products):
    product_slugs = []
    for product in products:
        cache_key = f'product_{product.slug}'
        product_data = ProductSerializer(product).data
        cache.set(cache_key, product_data, timeout=settings.CACHE_TIMEOUT)
        product_slugs.append(product.slug)
    # Cache the product slugs list
    cache.set(PRODUCT_SLUGS_KEY, product_slugs, timeout=settings.CACHE_TIMEOUT)


def cache_category_list(categories):
    category_slugs = []
    for category in categories:
        cache_key = f'category_{category.slug}'
        category_data = CategorySerializer(category).data
        cache.set(cache_key, category_data, timeout=settings.CACHE_TIMEOUT)
        category_slugs.append(category.slug)
    # Cache the category slugs list
    cache.set(CATEGORY_SLUGS_KEY, category_slugs, timeout=settings.CACHE_TIMEOUT)


def get_cached_product_slugs():
    product_slugs = cache.get(PRODUCT_SLUGS_KEY)

    if not product_slugs:
        products = list(Product.objects.all())
        cache_product_list(products)
        product_slugs = [product.slug for product in products]

    return product_slugs


def get_cached_category_slugs():
    category_slugs = cache.get(CATEGORY_SLUGS_KEY)

    if not category_slugs:
        categories = list(Category.objects.all())
        cache_category_list(categories)
        category_slugs = [category.slug for category in categories]

    return category_slugs


def update_product_cache(sender, instance, **kwargs):
    """
    Update the product cache with the serialized version of the product.
    This method can be called from both the Product and Stock models.
    """
    cache_key = f'product_{instance.slug}'

    # Serialize the product instance
    serialized_product = ProductSerializer(instance).data

    # Cache the serialized product data
    cache.set(cache_key, serialized_product, timeout=settings.CACHE_TIMEOUT)  # Cache updated product

    # Update the cached list of product slugs
    product_slugs = get_cached_product_slugs()
    if instance.slug not in product_slugs:
        product_slugs.append(instance.slug)
    cache.set(PRODUCT_SLUGS_KEY, product_slugs, timeout=settings.CACHE_TIMEOUT)


def delete_product_cache(sender, instance, **kwargs):
    """
    Remove the product from the cache when it is deleted.
    """
    cache_key = f'product_{instance.slug}'
    cache.delete(cache_key)  # Remove product from cache

    # Update the cached list of product slugs
    product_slugs = get_cached_product_slugs()
    if instance.slug in product_slugs:
        product_slugs.remove(instance.slug)
    cache.set(PRODUCT_SLUGS_KEY, product_slugs, timeout=settings.CACHE_TIMEOUT)


def update_category_cache(sender, instance, **kwargs):
    """
    Update the category cache and the category slug list.
    """
    cache_key = f'category_{instance.slug}'

    serialized_category = CategorySerializer(instance).data

    cache.set(cache_key, serialized_category, timeout=settings.CACHE_TIMEOUT)  # Cache updated category

    # Update the cached list of category slugs
    category_slugs = get_cached_category_slugs()
    if instance.slug not in category_slugs:
        category_slugs.append(instance.slug)
    cache.set(CATEGORY_SLUGS_KEY, category_slugs, timeout=settings.CACHE_TIMEOUT)


def delete_category_cache(sender, instance, **kwargs):
    """
    Remove the category from the cache when it is deleted.
    """
    cache_key = f'category_{instance.slug}'
    cache.delete(cache_key)  # Remove category from cache

    # Update the cached list of category slugs
    category_slugs = get_cached_category_slugs()
    if instance.slug in category_slugs:
        category_slugs.remove(instance.slug)
    cache.set(CATEGORY_SLUGS_KEY, category_slugs, timeout=settings.CACHE_TIMEOUT)

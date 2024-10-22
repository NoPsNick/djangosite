from django.conf import settings
from django.core.cache import cache
from django.db.models import Prefetch

from .serializers import ProductSerializer, CategorySerializer, StockSerializer
from .models import Category, Product, Stock

PRODUCT_SLUGS_KEY = 'product_slugs'
CATEGORY_SLUGS_KEY = 'category_slugs'


# Helper function to cache an object with a consistent timeout
def set_cache(cache_key, data):
    cache.set(cache_key, data, timeout=settings.CACHE_TIMEOUT)


# Function to retrieve or set cache for a product
def get_product_from_cache(slug):
    cache_key = f'product_{slug}'
    product_data = cache.get(cache_key)

    if not product_data:
        try:
            product = Product.objects.prefetch_related(
                Prefetch('stock')  # Prefetch related stock to minimize queries
            ).get(slug=slug)

            # Serialize and cache the product
            product_data = ProductSerializer(product).data
            set_cache(cache_key, product_data)

            # Cache stock information if it exists
            if product.stock:
                set_cache(f'stock_{slug}', StockSerializer(product.stock).data)

        except Product.DoesNotExist:
            return None

    return product_data


# Function to retrieve or set cache for stock
def get_stock_from_cache(slug):
    stock_cache_key = f'stock_{slug}'
    stock_data = cache.get(stock_cache_key)

    if stock_data is None:
        try:
            product = Product.objects.prefetch_related('stock').get(slug=slug)
            if product.stock:
                stock_data = StockSerializer(product.stock).data
                set_cache(stock_cache_key, stock_data)
        except Product.DoesNotExist:
            return False

    return stock_data


# Function to retrieve or set cache for a category
def get_category_from_cache(slug):
    cache_key = f'category_{slug}'
    category_data = cache.get(cache_key)

    if not category_data:
        try:
            category = Category.objects.get(slug=slug)
            category_data = CategorySerializer(category).data
            set_cache(cache_key, category_data)
        except Category.DoesNotExist:
            return None

    return category_data


# Function to cache the list of products and their stock information
def cache_product_list(products):
    product_slugs = []

    for product in products:
        cache_key = f'product_{product.slug}'
        product_data = ProductSerializer(product).data
        set_cache(cache_key, product_data)
        product_slugs.append(product.slug)

    # Cache the list of product slugs
    set_cache(PRODUCT_SLUGS_KEY, product_slugs)


# Function to cache the list of categories
def cache_category_list(categories):
    category_slugs = []

    for category in categories:
        cache_key = f'category_{category.slug}'
        category_data = CategorySerializer(category).data
        set_cache(cache_key, category_data)
        category_slugs.append(category.slug)

    # Cache the list of category slugs
    set_cache(CATEGORY_SLUGS_KEY, category_slugs)


# Retrieve or cache product slugs
def get_cached_product_slugs():
    product_slugs = cache.get(PRODUCT_SLUGS_KEY)

    if product_slugs is None:
        products = Product.objects.all().order_by('-id')
        cache_product_list(products)
        product_slugs = [product.slug for product in products]

    return product_slugs


# Retrieve or cache category slugs
def get_cached_category_slugs():
    category_slugs = cache.get(CATEGORY_SLUGS_KEY)

    if category_slugs is None:
        categories = Category.objects.all().order_by('-id')
        cache_category_list(categories)
        category_slugs = [category.slug for category in categories]

    return category_slugs


def update_product_cache(sender, instance, **kwargs):
    product_cache_key = f'product_{instance.slug}'
    stock_cache_key = f'stock_{instance.slug}'

    # Cache serialized product and stock
    set_cache(product_cache_key, ProductSerializer(instance).data)

    # Ensure that the stock instance is fully loaded and not an F expression
    if instance.stock:
        # Fetch the latest stock instance to avoid serialization issues
        stock_instance = Stock.objects.get(id=instance.stock.id)
        set_cache(stock_cache_key, StockSerializer(stock_instance).data)

    # Update the cached product slugs list
    product_slugs = get_cached_product_slugs()
    if instance.slug not in product_slugs:
        product_slugs.append(instance.slug)
    set_cache(PRODUCT_SLUGS_KEY, product_slugs)


# Delete product cache when the product or stock is deleted
def delete_product_cache(sender, instance, **kwargs):
    product_cache_key = f'product_{instance.slug}'
    stock_cache_key = f'stock_{instance.slug}'

    cache.delete(product_cache_key)
    cache.delete(stock_cache_key)

    # Update the cached product slugs list
    product_slugs = get_cached_product_slugs()
    if instance.slug in product_slugs:
        product_slugs.remove(instance.slug)
    set_cache(PRODUCT_SLUGS_KEY, product_slugs)


# Update the category cache
def update_category_cache(sender, instance, **kwargs):
    category_cache_key = f'category_{instance.slug}'
    set_cache(category_cache_key, CategorySerializer(instance).data)

    # Update the cached category slugs list
    category_slugs = get_cached_category_slugs()
    if instance.slug not in category_slugs:
        category_slugs.append(instance.slug)
    set_cache(CATEGORY_SLUGS_KEY, category_slugs)


# Delete category cache when the category is deleted
def delete_category_cache(sender, instance, **kwargs):
    category_cache_key = f'category_{instance.slug}'
    cache.delete(category_cache_key)

    # Update the cached category slugs list
    category_slugs = get_cached_category_slugs()
    if instance.slug in category_slugs:
        category_slugs.remove(instance.slug)
    set_cache(CATEGORY_SLUGS_KEY, category_slugs)

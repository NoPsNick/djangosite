from django.conf import settings
from django.core.cache import cache
from django.db.models import Prefetch

from .serializers import ProductSerializer, CategorySerializer, StockSerializer
from .models import Category, Product, Stock

PRODUCTS_DICT_KEY = 'products_dict'
CATEGORIES_DICT_KEY = 'categories_dict'
STOCKS_DICT_KEY = 'stocks_dict'
PRODUCT_SLUGS_KEY = 'product_slugs'
CATEGORY_SLUGS_KEY = 'category_slugs'


# Helper function to cache an entire dictionary with a consistent timeout
def set_cache(key, dictionary):
    cache.set(key, dictionary, timeout=settings.CACHE_TIMEOUT)


# Function to retrieve or set cache for a product
def get_product_from_cache(slug):
    products_dict = cache.get(PRODUCTS_DICT_KEY, {})

    if slug not in products_dict:
        try:
            product = Product.objects.select_related('role_type').prefetch_related(
                Prefetch('stock')  # Prefetch related stock to minimize queries
            ).get(slug=slug)
            product.check_promotions()
            product_data = ProductSerializer(product).data
            products_dict[slug] = product_data
            set_cache(PRODUCTS_DICT_KEY, products_dict)
        except Product.DoesNotExist:
            return None

    return products_dict[slug]


# Function to retrieve or set cache for stock
def get_stock_from_cache(slug):
    stocks_dict = cache.get(STOCKS_DICT_KEY, {})

    if slug not in stocks_dict:
        try:
            product = Product.objects.select_related('role_type').prefetch_related(
                Prefetch('stock')  # Prefetch related stock to minimize queries
            ).get(slug=slug)
            if getattr(product, 'stock', None):
                stock_data = StockSerializer(product.stock).data
                stocks_dict[slug] = stock_data
                set_cache(STOCKS_DICT_KEY, stocks_dict)
        except Product.DoesNotExist:
            return None

    return stocks_dict.get(slug, None)


# Function to retrieve or set cache for a category
def get_category_from_cache(slug):
    categories_dict = cache.get(CATEGORIES_DICT_KEY, {})

    if slug not in categories_dict:
        try:
            category = Category.objects.get(slug=slug)
            category_data = CategorySerializer(category).data
            categories_dict[slug] = category_data
            set_cache(CATEGORIES_DICT_KEY, categories_dict)
        except Category.DoesNotExist:
            return None

    return categories_dict.get(slug, None)


# Updated bulk-loading function for products
def cache_product_list(products):
    products_dict = {product.slug: ProductSerializer(product).data for product in products}
    set_cache(PRODUCTS_DICT_KEY, products_dict)  # Cache all products as a dictionary
    set_cache(PRODUCT_SLUGS_KEY, list(products_dict.keys()))  # Cache slugs as a separate list for quick access


# Updated bulk-loading function for categories
def cache_category_list(categories):
    categories_dict = {category.slug: CategorySerializer(category).data for category in categories}
    set_cache(CATEGORIES_DICT_KEY, categories_dict)  # Cache all categories as a dictionary
    set_cache(CATEGORY_SLUGS_KEY, list(categories_dict.keys()))  # Cache slugs as a separate list for quick access


# Update the product cache
def update_product_cache(sender, instance, **kwargs):
    instance.check_promotions()
    products_dict = cache.get(PRODUCTS_DICT_KEY, {})
    stocks_dict = cache.get(STOCKS_DICT_KEY, {})

    products_dict[instance.slug] = ProductSerializer(instance).data
    if hasattr(instance, 'stock'):
        try:
            stock_instance = Stock.objects.select_related('product').get(id=instance.stock.id)
            stocks_dict[instance.slug] = StockSerializer(stock_instance).data
        except Stock.DoesNotExist:
            pass

    set_cache(PRODUCTS_DICT_KEY, products_dict)
    set_cache(STOCKS_DICT_KEY, stocks_dict)


# Delete product and stock cache entries when the product or stock is deleted
def delete_product_cache(sender, instance, **kwargs):
    products_dict = cache.get(PRODUCTS_DICT_KEY, {})
    stocks_dict = cache.get(STOCKS_DICT_KEY, {})

    products_dict.pop(instance.slug, None)
    stocks_dict.pop(instance.slug, None)

    set_cache(PRODUCTS_DICT_KEY, products_dict)
    set_cache(STOCKS_DICT_KEY, stocks_dict)


# Update the category cache
def update_category_cache(sender, instance, **kwargs):
    # Cache the updated category
    category_cache_key = f'category_{instance.slug}'
    set_cache(category_cache_key, CategorySerializer(instance).data)

    # Find all products in the updated category
    products_in_category = (Product.objects.filter(category=instance).select_related('category', 'role_type')
    .prefetch_related('stock', 'promotions')
    )

    # Delete cache for each product and its stock in the category
    for product in products_in_category:
        product_cache_key = f'product_{product.slug}'
        stock_cache_key = f'stock_{product.slug}'

        # Remove product and stock cache entries
        cache.delete(product_cache_key)
        cache.delete(stock_cache_key)

    # Optionally, refresh the cached product slugs list
    product_slugs = get_cached_product_slugs()
    updated_product_slugs = [
        slug for slug in product_slugs if not products_in_category.filter(slug=slug).exists()
    ]
    set_cache(PRODUCTS_DICT_KEY, updated_product_slugs)

    # Optionally refresh the category slug cache list
    category_slugs = get_cached_category_slugs()
    if instance.slug not in category_slugs:
        category_slugs.append(instance.slug)
    set_cache(PRODUCTS_DICT_KEY, category_slugs)


# Delete category cache when the category is deleted
def delete_category_cache(sender, instance, **kwargs):
    categories_dict = cache.get(CATEGORIES_DICT_KEY, {})
    categories_dict.pop(instance.slug, None)
    set_cache(CATEGORIES_DICT_KEY, categories_dict)


# Retrieve or cache product slugs
def get_cached_product_slugs():
    products_dict = cache.get(PRODUCTS_DICT_KEY, {})

    # If the dictionary is empty, populate it from the database
    if not products_dict:
        products = (Product.objects.all().select_related('category', 'role_type')
                    .prefetch_related('stock', 'promotions').order_by('-id'))
        cache_product_list(products)
        products_dict = cache.get(PRODUCTS_DICT_KEY, {})

    # Extract slugs from the dictionary keys
    return list(products_dict.keys())


# Retrieve or cache category slugs
def get_cached_category_slugs():
    categories_dict = cache.get(CATEGORIES_DICT_KEY, {})

    # If the dictionary is empty, populate it from the database
    if not categories_dict:
        categories = Category.objects.all().order_by('-id')
        cache_category_list(categories)
        categories_dict = cache.get(CATEGORIES_DICT_KEY, {})

    # Extract slugs from the dictionary keys
    return list(categories_dict.keys())

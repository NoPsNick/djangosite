from django.db import models
from django.conf import settings
from django.core.cache import cache

PRODUCTS_DICT_KEY = 'products_dict'

CATEGORIES_DICT_KEY = 'categories_dict'


def set_cache(key, dictionary):
    cache.set(key, dictionary, timeout=getattr(settings, 'CACHE_TIMEOUT', (60 * 60 * 24 * 7)))


class ProductManager(models.Manager):

    def get_products_dict_from_cache(self):
        products_dict = cache.get(PRODUCTS_DICT_KEY, None)

        if products_dict is None:
            products_dict = self._get_all_products()
        return products_dict

    def get_product_from_cache(self, slug):
        product_dict = self.get_products_dict_from_cache()

        if slug not in product_dict:
            product_dict = self._get_all_products()
        return product_dict[slug]

    def get_stock_from_product(self, slug):
        product_dict = self.get_products_dict_from_cache()

        if slug not in product_dict:
            product_dict = self._get_all_products()
        stock = getattr('stock', product_dict[slug], None)
        return stock

    def _get_all_products(self):
        from .serializers import ProductSerializer
        products = (self.all().select_related('category', 'role_type')
                    .prefetch_related('stock', 'promotions').order_by('-id'))
        products_dict = {product.slug: ProductSerializer(product).data for product in products}
        set_cache(PRODUCTS_DICT_KEY, products_dict)  # Cache all products as a dictionary
        return products_dict

    def update_product_cache(self, slug):
        from .serializers import ProductSerializer
        product = self.select_related('category', 'role_type').prefetch_related('stock', 'promotions').get(slug=slug)
        products_dict = self.get_products_dict_from_cache()
        if product.slug not in products_dict:
            self._get_all_products()
        else:
            products_dict[product.slug] = ProductSerializer(product).data
            set_cache(PRODUCTS_DICT_KEY, products_dict)

    def delete_product_cache(self, slug):
        products_dict = self.get_products_dict_from_cache()
        products_dict.pop(slug, None)
        set_cache(PRODUCTS_DICT_KEY, products_dict)

    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)


class CategoryManager(models.Manager):
    def get_categories_dict_from_cache(self):
        categories_dict = cache.get(CATEGORIES_DICT_KEY, None)
        if categories_dict is None:
            categories_dict = self._get_all_categories()
            set_cache(CATEGORIES_DICT_KEY, categories_dict)
        return categories_dict

    def get_category_from_cache(self, slug):
        categories_dict = self.get_categories_dict_from_cache()
        if slug not in categories_dict:
            categories_dict = self._get_all_categories()
        return categories_dict[slug]

    def update_category_cache(self, slug):
        from .serializers import CategorySerializer
        categories_dict = self.get_categories_dict_from_cache()
        category = self.get(slug=slug)
        if category.slug not in categories_dict:
            self._get_all_categories()
        else:
            categories_dict[category.slug] = CategorySerializer(category).data
            set_cache(CATEGORIES_DICT_KEY, categories_dict)

    def delete_category_cache(self, slug):
        categories_dict = self.get_categories_dict_from_cache()
        categories_dict.pop(slug, None)
        set_cache(CATEGORIES_DICT_KEY, categories_dict)

    def _get_all_categories(self):
        from .serializers import CategorySerializer
        categories = (self.all().order_by('-id'))
        categories_dict = {category.slug: CategorySerializer(category).data for category in categories}
        set_cache(CATEGORIES_DICT_KEY, categories_dict)
        return categories_dict

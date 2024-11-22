import logging

from django.db import models, transaction
from django.conf import settings
from django.core.cache import cache

PRODUCTS_DICT_KEY = 'products_dict'

CATEGORIES_DICT_KEY = 'categories_dict'

PROMOTIONS_DICT_KEY = 'promotions_dict'

logger = logging.getLogger('celery')


def set_cache(key, dictionary):
    try:
        cache.set(key, dictionary, timeout=getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7))
    except Exception as e:
        # Loga o erro e continua sem interromper
        logger.error(f"Failed to set cache for key {key}: {e}")


class ProductManager(models.Manager):
    def get_products_dict_from_cache(self):
        products_dict = cache.get(PRODUCTS_DICT_KEY, None)

        if products_dict is None:
            products_dict = self._get_all_products()
        return products_dict

    def get_product_from_cache(self, slug):
        products_dict = self.get_products_dict_from_cache()
        product = products_dict.get(slug, None) or self._get_all_products().get(slug, None)
        if not product:
            raise KeyError(f"Produto não encontrado")
        return product

    def get_stock_from_product(self, slug):
        product_dict = self.get_products_dict_from_cache()

        if slug not in product_dict:
            product_dict = self._get_all_products()
        stock = getattr(product_dict[slug], 'stock', None)
        return stock

    def _get_all_products(self):
        from .serializers import ProductSerializer
        products = (
            self.all()
            .select_related('category', 'role_type')
            .prefetch_related('stock', 'promotions')
            .order_by('-id')
        )
        products_dict = {product.slug: ProductSerializer(product).data for product in products}
        set_cache(PRODUCTS_DICT_KEY, products_dict)
        return products_dict

    def update_product_cache(self, product):
        from .serializers import ProductSerializer
        try:
            products_dict = self.get_products_dict_from_cache()

            if products_dict.get(product.slug, None):
                products_dict[product.slug] = ProductSerializer(product).data
                set_cache(PRODUCTS_DICT_KEY, products_dict)
            else:
                self._get_all_products()
        except Exception as e:
            logger.error(f"Failed to update product cache for slug {product.slug}: {e}")

    def delete_product_cache(self, slug):
        products_dict = self.get_products_dict_from_cache() or {}
        products_dict.pop(slug, None)
        set_cache(PRODUCTS_DICT_KEY, products_dict)

    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)

    @transaction.atomic
    def update_promotion_product_price(self, slug, new_price):
        try:
            product = self.select_for_update().get(slug=slug)
            product.price = new_price
            product.save()
        except Exception as e:
            logger.error(f"Failed to update product price for slug {slug}: {e}")


class CategoryManager(models.Manager):
    def get_categories_dict_from_cache(self):
        categories_dict = cache.get(CATEGORIES_DICT_KEY, None)
        if categories_dict is None:
            categories_dict = self._get_all_categories()
        return categories_dict

    def get_category_from_cache(self, slug):
        categories_dict = self.get_categories_dict_from_cache()
        category = categories_dict.get(slug, None) or self._get_all_categories().get(slug, None)
        if not category:
            raise KeyError('Categoria não encontrada.')
        return category

    def update_category_cache(self, category):
        from .serializers import CategorySerializer
        categories_dict = self.get_categories_dict_from_cache()
        if category.slug not in categories_dict:
            self._get_all_categories()
        else:
            categories_dict[category.slug] = CategorySerializer(category).data
            set_cache(CATEGORIES_DICT_KEY, categories_dict)

    def delete_category_cache(self, slug):
        categories_dict = self.get_categories_dict_from_cache() or {}
        categories_dict.pop(slug, None)
        set_cache(CATEGORIES_DICT_KEY, categories_dict)

    def _get_all_categories(self):
        from .serializers import CategorySerializer
        categories = self.all().order_by('-id')
        categories_dict = {category.slug: CategorySerializer(category).data for category in categories}
        set_cache(CATEGORIES_DICT_KEY, categories_dict)
        return categories_dict


class PromotionManager(models.Manager):
    def get_promotions_dict_from_cache(self):
        promotions_dict = cache.get(PROMOTIONS_DICT_KEY, None)

        if promotions_dict is None:
            promotions_dict = self._get_all_promotions()
        return promotions_dict

    def _get_all_promotions(self):
        from .serializers import PromotionSerializer
        promotions = self.all().select_related('product').order_by('starts_at', 'created')
        promotions_dict = {promotion.id: PromotionSerializer(promotion).data for promotion in promotions}
        set_cache(PROMOTIONS_DICT_KEY, promotions_dict)
        return promotions_dict

    def update_promotion_cache(self, promotion_id):
        from .serializers import PromotionSerializer

        promotion = self.get(id=promotion_id).select_related('product')
        promotions_dict = self.get_promotions_dict_from_cache()
        if promotion.id not in promotions_dict:
            self._get_all_promotions()
        else:
            promotions_dict[promotion_id] = PromotionSerializer(promotion).data
            set_cache(PROMOTIONS_DICT_KEY, promotions_dict)
        self.promotion_check(promotion)


    def delete_promotion_cache(self, promotion_id):
        promotions_dict = self.get_promotions_dict_from_cache() or {}
        promotions_dict.pop(promotion_id, None)
        set_cache(PROMOTIONS_DICT_KEY, promotions_dict)

    @staticmethod
    def promotion_check(promotion):
        from .models import Promotion, Product
        try:
            if promotion.status == Promotion.ATIVO:
                Product.objects.update_promotion_product_price(promotion.product.slug, promotion.changed_price)
            elif promotion.status == Promotion.EXPIRADO:
                Product.objects.update_promotion_product_price(promotion.product.slug, promotion.original_price)
        except Exception as e:
            logger.error(f"Failed to update product price for promotion {promotion.id}: {e}")

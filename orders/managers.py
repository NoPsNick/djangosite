from django.contrib.auth import get_user_model
from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.core.paginator import Paginator

User = get_user_model()


class OrderManager(models.Manager):
    CACHE_TIMEOUT = getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7)

    def _get_prefetched_queryset(self):
        """
        Centralized method for query optimization with prefetch/related selects.
        """
        return self.select_related('customer').prefetch_related(
            'items'
        )

    @staticmethod
    def get_cache_key(customer_id):
        """
        Centralized cache key generation.
        """
        from .services import orders_cache_key_builder
        return orders_cache_key_builder(customer_id)

    def get_cached_orders(self, customer):
        """
        Retrieves cached orders or queries and caches them in bulk.
        """
        from .serializers import OrderSerializer
        cache_key = self.get_cache_key(customer.id)
        cached_orders = cache.get(cache_key)

        if cached_orders is None:
            orders = self._get_prefetched_queryset().filter(customer_id=customer.id).order_by('-id')
            cached_orders = {
                order.id: OrderSerializer(order).data
                for order in orders
            }
            cache.set(cache_key, cached_orders, timeout=self.CACHE_TIMEOUT)

        return cached_orders

    def get_cached_order(self, order_id, customer):
        """
        Retrieves a single cached order or fetches it from the database.
        """
        cache_key = self.get_cache_key(customer.id)
        cached_orders = cache.get(cache_key)

        if not cached_orders:
            cached_orders = self.get_cached_orders(customer)

        order = cached_orders.get(order_id)
        if not order:
            # Fetch from DB and cache it
            order_instance = self._get_prefetched_queryset().filter(customer=customer, id=order_id).first()
            if order_instance:
                order = self.cache_single_order(order_instance)

        return order

    def cache_single_order(self, order_instance):
        """
        Caches a single order into the bulk cache.
        """
        from .serializers import OrderSerializer
        cache_key = self.get_cache_key(order_instance.customer.id)
        cached_orders = self.get_cached_orders(order_instance.customer)

        order_data = OrderSerializer(order_instance).data
        cached_orders[order_instance.id] = order_data
        cache.set(cache_key, cached_orders, timeout=self.CACHE_TIMEOUT)

        return order_data

    def update_cached_orders(self, order):
        """
        Updates or adds an order to the cache.
        """
        self.cache_single_order(order)

    def delete_cached_order(self, order):
        """
        Removes an order from the cache.
        """
        cache_key = self.get_cache_key(order.customer.id)
        cached_orders = cache.get(cache_key) or {}

        if order.id in cached_orders:
            del cached_orders[order.id]
            cache.set(cache_key, cached_orders, timeout=self.CACHE_TIMEOUT)

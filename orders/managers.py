from django.contrib.auth import get_user_model
from django.db import models
from django.core.cache import cache
from django.conf import settings

User = get_user_model()


class OrderManager(models.Manager):

    def get_cached_orders(self, customer: User):
        """
        Retrieves the cached list of orders for a customer.
        Caches all orders in bulk if not cached.
        """
        from orders.serializers import OrderSerializer
        cache_key = f'orders_{customer.id}_dict'
        cached_orders = cache.get(cache_key)

        if cached_orders is None:
            orders_query_set = self.filter(customer=customer).order_by('-id')
            cached_orders = {}

            for order_instance in orders_query_set:
                order_data = OrderSerializer(order_instance).data
                cached_orders[order_instance.id] = order_data

            # Cache all orders as a dictionary with their IDs as keys
            cache.set(cache_key, cached_orders, timeout=getattr(settings, 'CACHE_TIMEOUT', 300))

        return list(cached_orders.values())

    def get_cached_order(self, order_id, customer: User):
        """
        Retrieves a single order for a customer from cache.
        Falls back to database if not cached.
        """
        cache_key = f'orders_{customer.id}_dict'
        cached_orders = cache.get(cache_key)

        if cached_orders is None:
            # Cache miss for the bulk data, so populate it
            self.get_cached_orders(customer)
            cached_orders = cache.get(cache_key)  # Retrieve again after caching

        # Retrieve the specific order by ID from the cached bulk data
        order = cached_orders.get(order_id)

        if order is None:
            # Fallback to querying the database if the order is not found in cache
            order_instance = self.get(customer=customer, id=order_id)
            order = self._cache_single_order(order_instance)

        return order

    @staticmethod
    def _cache_single_order(order_instace):
        """
        Helper method to add a single order to the cached bulk data if missing.
        """
        from orders.serializers import OrderSerializer
        cache_key = f'orders_{order_instace.customer.id}_dict'
        cached_orders = cache.get(cache_key) or {}

        order_data = OrderSerializer(order_instace).data
        cached_orders[order_instace.id] = order_data

        # Update the bulk cache with the new order data
        cache.set(cache_key, cached_orders, timeout=getattr(settings, 'CACHE_TIMEOUT', 300))

        return order_data

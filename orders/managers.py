from django.db import models
from django.core.cache import cache
from django.conf import settings

class OrderManager(models.Manager):

    def get_cached_orders(self, customer):
        """
        Retrieves the cached list of orders for a customer.
        Caches all orders in bulk if not cached.
        """
        from orders.serializers import OrderSerializer
        cache_key = f'orders_{customer.id}_list'
        orders = cache.get(cache_key)

        if orders is None:
            orders_query_set = self.filter(customer=customer).order_by('-id')
            serializer = OrderSerializer(orders_query_set, many=True)
            orders = serializer.data

            # Cache the full list of orders
            cache.set(cache_key, orders, timeout=getattr(settings, 'CACHE_TIMEOUT', 300))

            # Cache each order individually after it has been serialized
            for order_instance in orders_query_set:
                self._cache_single_order(order_instance)

        return orders

    def get_cached_order(self, order_id, customer):
        """
        Retrieves a single order for a customer from cache.
        Falls back to database if not cached.
        """
        cache_key = f'order_{customer.id}_{order_id}'
        order = cache.get(cache_key)

        if order is None:
            # Fallback to querying the database if not found in cache
            order_instance = self.get(customer=customer, id=order_id)
            order = self._cache_single_order(order_instance)

        return order

    @staticmethod
    def _cache_single_order(order):
        """
        Helper method to cache a single order after it has been fully serialized.
        """
        from orders.serializers import OrderDetailSerializer
        order_data = OrderDetailSerializer(order).data

        # Ensure that the cache only stores fully serialized data
        cache_key = f'order_{order.customer.id}_{order.id}'
        cache.set(cache_key, order_data, timeout=getattr(settings, 'CACHE_TIMEOUT', 300))

        return order_data  # Return the fully serialized cached data

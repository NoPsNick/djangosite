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
        cache_key = f'orders_{customer}_list'
        orders = cache.get(cache_key)

        if orders is None:
            orders_query_set = self.filter(customer=customer).order_by('-id')
            serializer = OrderSerializer(orders_query_set, many=True)
            orders = serializer.data

            # Cache the full list of orders in one go
            cache.set(cache_key, orders, timeout=settings.CACHE_TIMEOUT)

            # Optionally cache individual orders as well
            for order in orders_query_set:
                self._cache_single_order(order.id, order.customer, order_data=serializer.data)

        return orders

    def get_cached_order(self, id, customer):
        """
        Retrieves a single order for a customer from cache.
        Falls back to database if not cached.
        """
        from orders.serializers import OrderSerializer
        cache_key = f'order_{customer}_{id}'
        order = cache.get(cache_key)

        if order is None:
            order_instance = self.get(customer=customer, id=id)
            serializer = OrderSerializer(order_instance)
            order = serializer.data

            # Cache individual order
            self._cache_single_order(id, customer, order_data=order)

        return order

    @staticmethod
    def _cache_single_order(id, customer, order_data):
        """
        Helper method to cache a single order.
        """
        cache_key = f'order_{customer}_{id}'
        cache.set(cache_key, order_data, timeout=settings.CACHE_TIMEOUT)


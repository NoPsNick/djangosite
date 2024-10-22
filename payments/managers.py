from django.db import models
from django.core.cache import cache
from django.conf import settings


class PaymentManager(models.Manager):

    def get_cached_payments(self, customer):
        """
        Retrieves the cached list of payments for a customer.
        Caches all payments in bulk if not cached.
        """
        from .serializers import PaymentSerializer
        cache_key = f'payments_{customer.id}_list'
        payments = cache.get(cache_key)

        if payments is None:
            payments_query_set = self.filter(customer=customer).order_by('-id')
            serializer = PaymentSerializer(payments_query_set, many=True)
            payments = serializer.data

            # Cache the entire list of payments
            cache.set(cache_key, payments, timeout=getattr(settings, 'CACHE_TIMEOUT', 300))

            # Cache each payment individually
            for payment_instance in payments_query_set:
                self._cache_single_payment(payment_instance)

        return payments

    def get_cached_payment(self, payment_id, customer):
        """
        Retrieves a single payment for a customer from cache.
        Falls back to database if not cached.
        """
        cache_key = f'payment_{customer.id}_{payment_id}'
        payment = cache.get(cache_key)

        if payment is None:
            # Fallback to querying the database if not found in cache
            payment_instance = self.get(customer=customer, id=payment_id)
            payment = self._cache_single_payment(payment_instance)

        return payment

    @staticmethod
    def _cache_single_payment(payment):
        """
        Helper method to cache a single payment.
        """
        from .serializers import PaymentDetailSerializer
        payment_data = PaymentDetailSerializer(payment).data

        cache_key = f'payment_{payment.customer.id}_{payment.id}'
        cache.set(cache_key, payment_data, timeout=getattr(settings, 'CACHE_TIMEOUT', 300))

        return payment_data  # Return the cached data for consistency

from django.contrib.auth import get_user_model
from django.db import models
from django.core.cache import cache
from django.conf import settings

User = get_user_model()


class PaymentManager(models.Manager):
    CACHE_TIMEOUT = getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7)

    def _get_prefetched_queryset(self):
        """
        Centralized query optimization logic with related fields and prefetching.
        """
        return self.select_related(
            'customer',       # Fetch the customer from the Payment
            'order',          # Fetch the order from the Payment
            'payment_method', # Fetch the payment method from the Payment
        ).prefetch_related(
            'used_coupons'    # Pre-fetch the coupons that were used
        )

    @staticmethod
    def get_cache_key(customer_id):
        """
        Centralized cache key generation.
        """
        from .services import payments_cache_key_builder
        return payments_cache_key_builder(customer_id)

    def get_cached_payments(self, customer):
        """
        Retrieves cached payments or queries and caches them in bulk.
        """
        from .serializers import PaymentSerializer
        cache_key = self.get_cache_key(customer.id)
        cached_payments = cache.get(cache_key)

        if cached_payments is None:
            payments = self._get_prefetched_queryset().filter(customer=customer).order_by('-id')
            cached_payments = {
                payment.id: PaymentSerializer(payment).data
                for payment in payments
            }
            cache.set(cache_key, cached_payments, timeout=self.CACHE_TIMEOUT)

        return cached_payments

    def get_cached_payment(self, payment_id, customer):
        """
        Retrieves a single cached payment or fetches it from the database.
        """
        cache_key = self.get_cache_key(customer.id)
        cached_payments = cache.get(cache_key)

        if not cached_payments:
            cached_payments = self.get_cached_payments(customer)

        payment = cached_payments.get(payment_id)
        if not payment:
            # Fetch from DB and cache it
            payment_instance = self._get_prefetched_queryset().filter(customer=customer, id=payment_id).first()
            if payment_instance:
                payment = self._cache_single_payment(payment_instance)

        return payment

    def _cache_single_payment(self, payment_instance):
        """
        Caches a single payment into the bulk cache.
        """
        from .serializers import PaymentSerializer
        cache_key = self.get_cache_key(payment_instance.customer.id)
        cached_payments = self.get_cached_payments(payment_instance.customer)

        payment_data = PaymentSerializer(payment_instance).data
        cached_payments[payment_instance.id] = payment_data
        cache.set(cache_key, cached_payments, timeout=self.CACHE_TIMEOUT)

        return payment_data

    def update_cached_payment(self, payment):
        """
        Updates or adds a payment to the cache.
        """
        self._cache_single_payment(payment)

    def delete_cached_payment(self, payment):
        """
        Removes a payment from the cache.
        """
        cache_key = self.get_cache_key(payment.customer.id)
        cached_payments = cache.get(cache_key) or {}

        if payment.id in cached_payments:
            del cached_payments[payment.id]
            cache.set(cache_key, cached_payments, timeout=self.CACHE_TIMEOUT)

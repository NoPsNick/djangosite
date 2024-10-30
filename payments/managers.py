from django.contrib.auth import get_user_model
from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.db.models import Prefetch

from orders.models import Item

User = get_user_model()


class PaymentManager(models.Manager):

    def get_cached_payments(self, customer: User):
        """
        Retrieves the cached list of payments for a customer.
        Caches all payments in bulk if not cached.
        """
        from .serializers import PaymentSerializer
        from .services import payments_cache_key_builder
        cache_key = payments_cache_key_builder(customer.id)
        cached_payments = cache.get(cache_key)

        if cached_payments is None:
            payments_query_set = self.filter(customer=customer).select_related(
                'customer', # Fetch the customer from the Payment
                'order', # Fetch the order from the Payment
                'payment_method', # Fetch the payment method from the Payment
            ).prefetch_related(
                # Pre-fetch the payment order items(products)
                Prefetch('order__items', queryset=Item.objects.select_related('product__category')),
                'order__customer', # Pre-fetch the payment order
                'used_coupons__codes' # Pre-fetch the coupons that were used.
            ).order_by('-id')
            cached_payments = {}

            # Serialize and store each payment in a dictionary with payment ID as key
            for payment_instance in payments_query_set:
                payment_data = PaymentSerializer(payment_instance).data
                cached_payments[payment_instance.id] = payment_data

            # Cache all payments as a dictionary
            cache.set(cache_key, cached_payments, timeout=getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7))

        return list(cached_payments.values())

    def get_cached_payment(self, payment_id, customer: User):
        """
        Retrieves a single payment for a customer from cache.
        Falls back to database if not cached.
        """
        from .services import payments_cache_key_builder
        cache_key = payments_cache_key_builder(customer.id)
        cached_payments = cache.get(cache_key)

        if cached_payments is None:
            # If the bulk cache is missing, populate it
            self.get_cached_payments(customer)
            cached_payments = cache.get(cache_key)  # Retrieve again after populating the cache

        # Retrieve the specific payment by ID from the cached bulk data
        payment = cached_payments.get(payment_id)

        if payment is None:
            # Fallback to querying the database if the payment is not in cache
            payment_instance = self.filter(customer=customer, id=payment_id).select_related(
                'customer', # Fetch the customer from the Payment
                'order', # Fetch the order from the Payment
                'payment_method', # Fetch the payment method from the Payment
            ).prefetch_related(
                # Pre-fetch the payment order items(products)
                Prefetch('order__items', queryset=Item.objects.select_related('product__category')),
                'order__customer', # Pre-fetch the payment order
                'used_coupons__codes' # Pre-fetch the coupons that were used.
            )
            payment = self._cache_single_payment(payment_instance)

        return payment

    @staticmethod
    def _cache_single_payment(payment_instance):
        """
        Helper method to add a single payment to the cached bulk data if it's missing.
        """
        from .services import payments_cache_key_builder
        from .serializers import PaymentSerializer
        cache_key = payments_cache_key_builder(payment_instance.customer.id)
        cached_payments = cache.get(cache_key) or {}

        # Serialize the payment data
        payment_data = PaymentSerializer(payment_instance).data
        cached_payments[payment_instance.id] = payment_data

        # Update the bulk cache with the new payment data
        cache.set(cache_key, cached_payments, timeout=getattr(settings, 'CACHE_TIMEOUT', 60 * 60 * 24 * 7))

        return payment_data

from django.contrib import admin
from .models import ExternalApiResponse, PaymentMethod, Payment, PaymentPromotionCode
from django.utils.translation import gettext_lazy as _


@admin.register(ExternalApiResponse)
class ExternalApiResponseAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'created', 'modified']
    search_fields = ['transaction_id']
    readonly_fields = ['created', 'modified']  # Keep timestamps read-only
    ordering = ['-created']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_type', 'created', 'modified']
    search_fields = ['name', 'payment_type']
    list_filter = ['payment_type']
    autocomplete_fields = ['response']  # Improve response field search
    ordering = ['name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'order', 'payment_method', 'amount', 'status', 'created', 'modified']
    list_filter = ['status', 'created', 'modified']
    search_fields = ['customer__username', 'order__id', 'status']
    autocomplete_fields = ['customer', 'order', 'payment_method']
    readonly_fields = ['created', 'modified']  # Keep timestamps read-only
    ordering = ['-created']

    def get_queryset(self, request):
        # Optimize queryset for performance by using select_related and prefetch_related
        queryset = super().get_queryset(request)
        return queryset.select_related('customer', 'order', 'payment_method')


@admin.register(PaymentPromotionCode)
class PaymentPromotionCodeAdmin(admin.ModelAdmin):
    list_display = ['payment', 'promotion_code', 'applied_at']
    search_fields = ['payment__id', 'promotion_code__code']
    autocomplete_fields = ['payment', 'promotion_code']
    readonly_fields = ['applied_at']
    ordering = ['-applied_at']

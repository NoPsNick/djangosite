from django.contrib import admin

from payments.models import PaymentMethod, PaymentPromotionCode, Payment, ExternalApiResponse


# Register your models here.
@admin.register(PaymentMethod)
class PaymentPromotionCodeAdmin(admin.ModelAdmin):
    pass


@admin.register(PaymentPromotionCode)
class PaymentPromotionCodeAdmin(admin.ModelAdmin):
    pass


@admin.register(Payment)
class ExternalApiResponseAdmin(admin.ModelAdmin):
    pass


@admin.register(ExternalApiResponse)
class ExternalApiResponseAdmin(admin.ModelAdmin):
    pass

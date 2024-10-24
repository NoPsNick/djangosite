from django.contrib import admin

from legaldocs.models import Contract, PrivacyPolicy, ReturnPolicy, TermOfService


@admin.register(Contract)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    pass


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    pass


@admin.register(ReturnPolicy)
class TermOfServiceAdmin(admin.ModelAdmin):
    pass


@admin.register(TermOfService)
class TermOfServiceAdmin(admin.ModelAdmin):
    pass

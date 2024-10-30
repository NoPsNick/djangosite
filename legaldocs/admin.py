from django.contrib import admin

from legaldocs.models import Contract, PrivacyPolicy, ReturnPolicy, TermOfService


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    readonly_fields = ['created', 'modified']  # Keep timestamps read-only
    ordering = ['-modified']


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    readonly_fields = ['created', 'modified']  # Keep timestamps read-only
    ordering = ['-modified']


@admin.register(ReturnPolicy)
class ReturnPolicyAdmin(admin.ModelAdmin):
    readonly_fields = ['created', 'modified']  # Keep timestamps read-only
    ordering = ['-modified']


@admin.register(TermOfService)
class TermOfServiceAdmin(admin.ModelAdmin):
    readonly_fields = ['created', 'modified']  # Keep timestamps read-only
    ordering = ['-modified']

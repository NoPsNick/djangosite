from django.contrib import admin

from users.models import User, Address, RoleType, Role, PhoneNumber


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Address)
class EnderecoAdmin(admin.ModelAdmin):
    pass


@admin.register(RoleType)
class RoleTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    pass
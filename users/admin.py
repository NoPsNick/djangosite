from django.contrib import admin

from users.models import User, RoleType, Role


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['id', 'username']


@admin.register(RoleType)
class RoleTypeAdmin(admin.ModelAdmin):
    search_fields = ["id", "name", 'description']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass

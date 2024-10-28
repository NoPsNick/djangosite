from django.contrib import admin
from django.contrib.auth.models import Permission
from django.db.models import Count, Prefetch

from .models import RoleType, Role, User


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    search_fields = ['name', 'codename', 'content_type__model']

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related('content_type')
        return queryset


class RoleInline(admin.TabularInline):
    model = Role
    fields = ['role_type', 'status', 'expires_at']
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ['created', 'modified', 'expires_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        # Use Prefetch to control loading of permissions with content types in a single query
        permissions_prefetch = Prefetch(
            'role_type__permissions',
            queryset=Permission.objects.select_related('content_type')
        )

        return queryset.select_related('user', 'role_type').prefetch_related(permissions_prefetch)


@admin.register(RoleType)
class RoleTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'currency', 'staff', 'effective_days']
    search_fields = ['name']
    list_filter = ['currency', 'staff']
    ordering = ['-modified']
    readonly_fields = ['created', 'modified']
    filter_horizontal = ['permissions']

    def get_queryset(self, request):
        # Annotate count on the queryset to avoid redundant counting
        queryset = super().get_queryset(request).prefetch_related(
            'permissions', 'permissions__content_type'
        ).annotate(permission_count=Count('permissions'))
        return queryset

    def get_search_results(self, request, queryset, search_term):
        # Override to remove redundant count operation on changelist view
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if use_distinct:
            queryset = queryset.distinct()
        return queryset, use_distinct

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Override permissions field to include prefetched content types, reducing redundant queries
        if db_field.name == 'permissions':
            kwargs['queryset'] = Permission.objects.select_related('content_type')
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role_type', 'status', 'expires_at', 'created']
    list_filter = ['status', 'role_type']
    search_fields = ['user__username', 'role_type__name']
    autocomplete_fields = ['user', 'role_type']
    ordering = ['-created']
    readonly_fields = ['created', 'modified']

    def get_queryset(self, request):
        # Use select_related for efficient related data loading
        return super().get_queryset(request).select_related('user', 'role_type')

    def get_search_results(self, request, queryset, search_term):
        # Avoid redundant count by overriding search results
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if use_distinct:
            queryset = queryset.distinct()
        return queryset, use_distinct


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'balance', 'tos_accept', 'birth_date', 'is_staff']
    search_fields = ['username', 'email']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    ordering = ['username']
    readonly_fields = ['last_login', 'date_joined']
    filter_horizontal = ['user_permissions']
    inlines = [RoleInline]

    def get_queryset(self, request):
        # Avoid duplicate queries by prefetching related data
        return super().get_queryset(request).select_related('role', 'role__role_type'
                                                            ).prefetch_related(
            Prefetch(
            'user_permissions',
            queryset=Permission.objects.select_related('content_type')),
        )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'birth_date', 'tos_accept')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Other Info', {'fields': ('balance',)}),
    )

    # Foi sofrido descobrir isso :)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Override user_permissions field to include prefetched content types, reducing redundant queries
        if db_field.name == 'user_permissions':
            kwargs['queryset'] = Permission.objects.select_related('content_type')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

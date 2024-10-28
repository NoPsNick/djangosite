from django.db import transaction
from django.utils import timezone


class RolePermissionService:

    @staticmethod
    def add_role_permissions(user, role_type):
        """
        Adds permissions from the given role type to the user.
        """
        with transaction.atomic():
            if role_type:
                for perm in role_type.permissions.all():
                    user.user_permissions.add(perm)
                user.save()

    @staticmethod
    def remove_role_permissions(user, role_type):
        """
        Removes permissions from the given role type from the user.
        """
        with transaction.atomic():
            if role_type:
                for perm in role_type.permissions.all():
                    user.user_permissions.remove(perm)
                user.save()

    def update_user_role(self, user, new_role=None):
        """
        Update the user's permissions based on their role.
        This method will remove old role permissions and add new ones.
        """
        with transaction.atomic():
            if getattr(user, 'role', None):
                # Remove current role permissions if the user has a role
                self.remove_role_permissions(user, user.role.role_type)

            if new_role:
                # Add new role permissions if a new role is provided
                self.add_role_permissions(user, new_role.role_type)

            user.role = new_role
            user.save(update_fields=['role'])

    def verify_role_status(self, user):
        """
        Verifies the status of the user's role and updates permissions accordingly.
        """
        with transaction.atomic():
            if getattr(user, 'role', None) and not user.role.is_expired():
                # The role is active, ensure permissions are in place
                self.add_role_permissions(user, user.role.role_type)
            elif getattr(user, 'role', None) and user.role.is_expired():
                # The role is expired, remove permissions
                self.remove_role_permissions(user, user.role.role_type)
                user.role = None  # Optionally set the role to None if expired
                user.save(update_fields=['role'])

    def expire_roles(self):
        """
        Check all roles and expire those that have passed their expiration date.
        """
        from .models import Role
        with transaction.atomic():
            expired_roles = Role.objects.filter(expires_at__lte=timezone.now(), status=Role.ATIVO)
            for role in expired_roles:
                role.status = Role.EXPIRADO
                role.save(update_fields=['status'])
                self.remove_role_permissions(role.user, role.role_type)

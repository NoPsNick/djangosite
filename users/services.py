from django.utils import timezone
from .models import Role


class RolePermissionService:

    @staticmethod
    def add_role_permissions(user, role_type):
        """
        Adds permissions from the given role type to the user.
        """
        if role_type:
            for perm in role_type.permissions.all():
                user.user_permissions.add(perm)
            user.save()

    @staticmethod
    def remove_role_permissions(user, role_type):
        """
        Removes permissions from the given role type from the user.
        """
        if role_type:
            for perm in role_type.permissions.all():
                user.user_permissions.remove(perm)
            user.save()

    def update_user_role(self, user, new_role=None):
        """
        Update the user's permissions based on their role.
        This method will remove old role permissions and add new ones.
        """
        if user.role:
            # Remove current role permissions if the user has a role
            self.remove_role_permissions(user, user.role.role_type)

        if new_role:
            # Add new role permissions if a new role is provided
            self.add_role_permissions(user, new_role.role_type)

        user.role = new_role
        user.save()

    def verify_role_status(self, user):
        """
        Verifies the status of the user's role and updates permissions accordingly.
        """
        if user.role and not user.role.is_expired():
            # The role is active, ensure permissions are in place
            self.add_role_permissions(user, user.role.role_type)
        else:
            # The role is expired, remove permissions
            self.remove_role_permissions(user, user.role.role_type)
            user.role = None  # Optionally set the role to None if expired
            user.save()

    def expire_roles(self):
        """
        Check all roles and expire those that have passed their expiration date.
        """
        expired_roles = Role.objects.filter(expires_at__lte=timezone.now(), status=Role.ATIVO)
        for role in expired_roles:
            role.status = Role.EXPIRADO
            role.save()
            self.remove_role_permissions(role.user, role.role_type)

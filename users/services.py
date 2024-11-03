from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone


class RolePermissionService:

    @staticmethod
    def update_user_role(user, new_role=None):
        """
        Update the user's permissions based on their role.
        This method will remove old role permissions and add new ones.
        """
        from .models import User, Role
        try:
            with transaction.atomic():
                locked_user = User.objects.select_for_update().get(pk=user.pk)
                if isinstance(new_role, Role):
                    locked_user.role = new_role
                    locked_user.save()
                else:
                    locked_user.role = None
                    locked_user.save()
        except Exception as e:
            raise ValidationError(str(e))

    @staticmethod
    def expire_roles():
        """
        Check all roles and expire those that have passed their expiration date.
        """
        from .models import Role
        try:
            with transaction.atomic():
                expired_roles = Role.objects.filter(expires_at__lte=timezone.now(), status=Role.ATIVO)
                for role in expired_roles:
                    role.status = Role.EXPIRADO
                    role.save()
        except Exception as e:
            raise ValidationError(str(e))

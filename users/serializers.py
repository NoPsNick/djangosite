from django.core.exceptions import PermissionDenied
from django.utils import timezone

from rest_framework import serializers

from .models import UserHistory, User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_info = serializers.SerializerMethodField()
    role_icon = serializers.SerializerMethodField()
    date_joined = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    is_authenticated = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'is_staff',
            'date_joined',
            'last_login',
            'is_active',
            'is_authenticated',
            'full_name',
            'role_info',
            'role_icon',
            'balance'
        ]

    def get_request(self):
        return self.context.get('request')

    def check_permission(self, obj):
        request = self.get_request()
        if not request:
            return None
        if request.is_staff:
            return True
        if request.id == obj.id:
            return True
        raise PermissionDenied('You cannot access this resource')

    def get_full_name(self, obj):
        if self.check_permission(obj):
            return obj.get_full_name() if obj.is_active else None

    def get_role_info(self, obj):
        if self.check_permission(obj):
            return obj.get_role_info()

    def get_role_icon(self, obj):
        if self.check_permission(obj):
            return obj.get_role_icon()

    def get_date_joined(self, obj):
        if self.check_permission(obj):
            date_joined = timezone.localtime(obj.date_joined) if obj.date_joined else None
            return date_joined.strftime("%d/%m/%Y") if date_joined else None

    def get_last_login(self, obj):
        if self.check_permission(obj):
            last_login = timezone.localtime(obj.last_login) if obj.last_login else None
            return last_login.strftime("%d/%m/%Y - %H:%M:%S") if last_login else None

    def get_is_staff(self, obj):
        if self.check_permission(obj):
            return obj.is_staff

    def get_is_active(self, obj):
        if self.check_permission(obj):
            return obj.is_active

    def get_is_authenticated(self, obj):
        if self.check_permission(obj):
            return obj.is_authenticated


class UserHistorySerializer(serializers.ModelSerializer):
    type_display = serializers.SerializerMethodField()
    class Meta:
        model = UserHistory
        fields = ['id', 'type_display', 'info', 'link']

    def get_type_display(self, obj):
        return obj.get_type_display()

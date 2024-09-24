from django.core.exceptions import PermissionDenied
from django.utils import timezone

from rest_framework import serializers

from .models import About
from products.models import Promotion
from users.models import User, Address, PhoneNumber


class PromotionSerializer(serializers.ModelSerializer):
    product_link = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    product_description = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    starts_at = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ['id',
                  'starts_at',
                  'expires_at',
                  'product_name',
                  'product_description',
                  'product_image',
                  'product_link',
                  'changed_price',
                  'original_price',
                  'status'
        ]

    def get_starts_at(self, obj):
        # Convert to the local time zone before formatting
        local_start_time = timezone.localtime(obj.starts_at)
        return local_start_time.strftime('%d/%m/%Y - %H:%M:%S')

    def get_expires_at(self, obj):
        # Convert to the local time zone before formatting
        local_expire_time = timezone.localtime(obj.expires_at)
        return local_expire_time.strftime('%d/%m/%Y - %H:%M:%S')

    def get_product_name(self, obj):
        return obj.product.name

    def get_product_description(self, obj):
        return obj.product.description

    def get_product_link(self, obj):
        return obj.product.get_absolute_url()

    def get_product_image(self, obj):
        return obj.product.image


class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_info = serializers.SerializerMethodField()
    role_icon = serializers.SerializerMethodField()
    date_joined = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
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
            'phone_number',
            'is_active',
            'is_authenticated',
            'address',
            'full_name',
            'role_info',
            'role_icon'
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
            return obj.role.get_role_info() if obj.role else None

    def get_role_icon(self, obj):
        if self.check_permission(obj):
            return obj.get_role_icon() if obj.role else None

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

    def get_phone_number(self, obj):
        if self.check_permission(obj):
            return PhoneNumber.objects.get_selected_phone_number(obj)

    def get_address(self, obj):
        if self.check_permission(obj):
            return Address.objects.get_selected_address(obj)

    def get_is_active(self, obj):
        if self.check_permission(obj):
            return obj.is_active

    def get_is_authenticated(self, obj):
        if self.check_permission(obj):
            return obj.is_authenticated


class AddressSerializer(serializers.ModelSerializer):
    absolute_url = serializers.SerializerMethodField()
    remove_url = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ['id', 'postal_code', 'rua', 'number', 'complement', 'district', 'state', 'city', 'selected',
                  'created', 'modified', 'full_address' ,'absolute_url', 'remove_url']

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()

    def get_remove_url(self, obj):
        return obj.get_remove_url()

    def get_full_address(self, obj):
        return obj.get_full_address()


class PhoneNumberSerializer(serializers.ModelSerializer):
    absolute_url = serializers.SerializerMethodField()
    remove_url = serializers.SerializerMethodField()

    class Meta:
        model = PhoneNumber
        fields = ['id', 'number', 'selected', 'created', 'modified', 'absolute_url', 'absolute_url', 'remove_url']

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()

    def get_remove_url(self, obj):
        return obj.get_remove_url()

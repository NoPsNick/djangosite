from django.utils import timezone
from rest_framework import serializers

from users.models import RoleType
from .models import Product, Category, Stock, Promotion


class RoleTypeSerializer(serializers.ModelSerializer):
    effective_days = serializers.CharField(source='effective_days.days', read_only=True)

    class Meta:
        model = RoleType
        fields = ['id', 'name', 'effective_days']


class ProductSerializer(serializers.ModelSerializer):
    link_absoluto = serializers.URLField(source='get_absolute_url', read_only=True)
    category = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    role = RoleTypeSerializer(source='role_type', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'is_available', 'image', 'slug', 'link_absoluto', 'category',
                  'role', 'is_role']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class StockSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = Stock
        fields = ['product', 'units']


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

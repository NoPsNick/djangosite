from rest_framework import serializers

from users.models import RoleType
from .models import Product, Category, Stock


class ProductSerializer(serializers.ModelSerializer):
    link_absoluto = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'is_available', 'image', 'slug', 'link_absoluto', 'category',
                  'role', 'is_role']

    def get_link_absoluto(self, obj):
        return obj.get_absolute_url()

    def get_category(self, obj):
        if obj.category is not None:
            return obj.category.slug
        return None

    def get_role(self, obj):
        if obj.role_type is not None:
            return RoleTypeSerializer(obj.role_type).data


class RoleTypeSerializer(serializers.ModelSerializer):
    effective_days = serializers.SerializerMethodField()
    class Meta:
        model = RoleType
        fields = ['id', 'name', 'effective_days']

    def get_effective_days(self, obj):
        # Convert effective_days from timedelta to a datetime string
        days = obj.effective_days.days
        return str(days) + " Dias"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class StockSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = Stock
        fields = ['product', 'units']

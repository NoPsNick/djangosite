from rest_framework import serializers

from users.models import RoleType
from .models import Product, Category, Stock


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

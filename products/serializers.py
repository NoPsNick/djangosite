from rest_framework import serializers
from .models import Product, Category, Stock


class ProductSerializer(serializers.ModelSerializer):
    link_absoluto = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'is_available', 'image', 'slug', 'link_absoluto', 'category']

    def get_link_absoluto(self, obj):
        return obj.get_absolute_url()

    def get_category(self, obj):
        return obj.category.slug


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class StockSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = Stock
        fields = ['product', 'units']

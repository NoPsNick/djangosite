from rest_framework import serializers
from orders.models import Order, Item
from products.serializers import ProductSerializer


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()  # Use MethodField to customize product data

    class Meta:
        model = Order
        fields = ['id', 'status', 'customer', 'total_amount', 'products']

    def get_total_amount(self, obj):
        return str(obj.get_total_amount())

    def get_status(self, obj):
        return obj.get_status_display()

    def get_customer(self, obj):
        return obj.customer.first_name if obj.customer.first_name else obj.customer.username

    def get_products(self, obj):
        items = obj.items.all()
        serializer = ItemSerializer(items, many=True)
        return serializer.data


class ItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()  # Nesting ProductSerializer to include product details
    full_price = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['product', 'quantity', 'full_price']
        read_only_fields = ['quantity']

    def get_full_price(self, obj):
        return str(obj.get_total_price())

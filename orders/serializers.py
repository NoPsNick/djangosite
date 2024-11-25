from rest_framework import serializers
from orders.models import Order, Item
from products.serializers import ProductSerializer


class ItemSerializer(serializers.ModelSerializer):
    full_price = serializers.DecimalField(source='get_total_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Item
        fields = ['name', 'price', 'quantity', 'full_price', 'slug']
        read_only_fields = ['quantity']


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display', read_only=True)
    total_amount = serializers.DecimalField(source='get_total_amount', max_digits=10, decimal_places=2, read_only=True)
    customer = serializers.CharField(source='customer.get_full_name', read_only=True)
    products = ItemSerializer(source='items', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'customer', 'total_amount', 'products']

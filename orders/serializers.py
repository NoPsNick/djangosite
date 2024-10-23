from rest_framework import serializers
from orders.models import Order, Item
from products.serializers import ProductSerializer


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

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
        # Explicitly fetch the related items and products
        items = obj.items.select_related('product').all()

        # Fully serialize the items with the ItemSerializer
        serializer = ItemSerializer(items, many=True)

        # Return fully serialized data
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

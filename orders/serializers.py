from rest_framework import serializers

from orders.models import Order


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id',
                  'status',
                  'customer',
                  'total_amount']

    def get_total_amount(self, obj):
        return str(obj.get_total_amount())

    def get_status(self, obj):
        return obj.get_status_display

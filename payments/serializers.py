from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    payment_method = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'customer', 'payment_method', 'amount', 'status']
        read_only_fields = ['id', 'amount', 'status']

    def get_payment_method(self, obj):
        return obj.payment_method.name if obj.payment_method.name else obj.payment_method.payment_type

    def get_customer(self, obj):
        return obj.customer.name


class PaymentDetailSerializer(serializers.ModelSerializer):
    payment_method = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()
    used_coupons = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'customer', 'payment_method', 'amount', 'status', 'order_id', 'used_coupons']
        read_only_fields = ['id', 'amount', 'status']

    def get_payment_method(self, obj):
        return obj.payment_method.name if obj.payment_method.name else obj.payment_method.payment_type

    def get_customer(self, obj):
        return obj.customer.name

    def get_order_id(self, obj):
        return obj.order.id

    def get_used_coupons(self, obj):
        coupons = obj.used_coupons.all()
        return [coupon.code for coupon in coupons]


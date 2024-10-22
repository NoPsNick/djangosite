from rest_framework import serializers
from .models import Payment
from orders.serializers import OrderDetailSerializer


class BasePaymentSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'customer', 'payment_method', 'amount', 'status']
        read_only_fields = ['id', 'amount']

    def get_payment_method(self, obj):
        return obj.payment_method.name.capitalize() if obj.payment_method.name else (
            obj.payment_method.payment_type.capitalize())

    def get_customer(self, obj):
        return obj.customer.first_name if obj.customer.first_name else obj.customer.username

    def get_status(self, obj):
        return obj.get_status_display()


class PaymentSerializer(BasePaymentSerializer):
    class Meta(BasePaymentSerializer.Meta):
        pass


class PaymentDetailSerializer(BasePaymentSerializer):
    order = OrderDetailSerializer()
    used_coupons = serializers.SerializerMethodField()

    class Meta(BasePaymentSerializer.Meta):
        fields = BasePaymentSerializer.Meta.fields + ['order', 'used_coupons']

    def get_used_coupons(self, obj):
        coupons = obj.used_coupons.all()
        return [coupon.code for coupon in coupons]

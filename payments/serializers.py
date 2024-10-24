from rest_framework import serializers
from .models import Payment
from orders.serializers import OrderSerializer


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer()
    used_coupons = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'customer', 'payment_method', 'amount', 'status', 'order', 'used_coupons']
        read_only_fields = ['id', 'amount']

    def get_payment_method(self, obj):
        # Aqui, utilizamos diretamente o campo pré-buscado
        if hasattr(obj, 'payment_method'):
            return obj.payment_method.name.capitalize() if obj.payment_method.name else (
                obj.payment_method.payment_type.capitalize()
            )
        return None

    def get_customer(self, obj):
        # Acessar customer diretamente evita consultas extras
        if hasattr(obj, 'customer'):
            return obj.customer.first_name if obj.customer.first_name else obj.customer.username
        return None

    def get_status(self, obj):
        return obj.get_status_display()

    def get_used_coupons(self, obj):
        coupons = obj.used_coupons.all()
        return [coupon.code for coupon in coupons]


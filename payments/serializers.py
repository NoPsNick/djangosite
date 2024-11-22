from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    used_coupons = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'customer', 'payment_method', 'amount', 'status', 'order', 'used_coupons']
        read_only_fields = ['id', 'amount']

    def get_payment_method(self, obj):
        # Aqui, utilizamos diretamente o campo pré-buscado
        return obj.payment_method.get_payment_type_display()

    def get_customer(self, obj):
        # Acessar customer diretamente evita consultas extras
        if hasattr(obj, 'customer'):
            return obj.customer.first_name if obj.customer.first_name else obj.customer.username
        return None

    def get_used_coupons(self, obj):
        coupons = obj.used_coupons.all()
        return [coupon.code for coupon in coupons]

    def get_order(self, obj):
        return obj.order.id

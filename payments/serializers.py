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
        return obj.customer.pk

    def get_used_coupons(self, obj):
        coupons = obj.used_coupons.all()
        coupons_dict = {}
        for coupon in coupons:
            if coupon.discount_amount:
                coupons_dict[coupon.code] = {'type': 'Desconto Bruto',
                                             'discount': f'-{coupon.discount_amount}'}
            elif coupon.discount_percentage:
                coupons_dict[coupon.code] = {'type': 'Desconto em Porcentagem',
                                             'discount': f'-{coupon.discount_percentage}%'}
        return coupons_dict

    def get_order(self, obj):
        return obj.order.id

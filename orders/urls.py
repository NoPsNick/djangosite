from django.urls import path
from .views import CreateOrderView, CreatePaymentView, UserOrderListView

app_name = "orders"


urlpatterns = [
    path('', UserOrderListView.as_view(), name='order_list'),
    path('criar-pedido/', CreateOrderView.as_view(), name='create_order'),
    path('pedidos/<int:order_id>/criar-pagamento/', CreatePaymentView.as_view(), name='create_payment'),
]

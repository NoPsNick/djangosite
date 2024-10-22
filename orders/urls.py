from django.urls import path
from .views import CreateOrderView, PaymentCreateView, UserOrderListView, UserOrderDetailView

app_name = "orders"


urlpatterns = [
    path('', UserOrderListView.as_view(), name='order_list'),
    path('criar-pedido/', CreateOrderView.as_view(), name='create_order'),
    path('<int:order_id>/', UserOrderDetailView.as_view(), name='order_detail'),
    path('<int:order_id>/criar-pagamento/', PaymentCreateView.as_view(), name='create_payment'),
]

from django.urls import path
from .views import UserPaymentListView, UserPaymentDetailView

app_name = "payments"


urlpatterns = [
    path('', UserPaymentListView.as_view(), name='payment_list'),
    path('<int:payment_id>/', UserPaymentDetailView.as_view(), name='payment_detail'),
]

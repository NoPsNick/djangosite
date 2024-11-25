from django.urls import path
from .views import CartAPIView, add_to_cart, remove_from_cart, CartView


app_name = "cart"

urlpatterns = [
    path('api/cart/', CartAPIView.as_view(), name='cart_api'),
    path('remover/<slug:slug>/', remove_from_cart, name='cart_remove'),
    path('adicionar/<slug:slug>/', add_to_cart, name='cart_add'),
    path('', CartView.as_view(), name='detail'),
]
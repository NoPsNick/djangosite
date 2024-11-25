from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import ProductListView, ProductDetailView

app_name = "products"


urlpatterns = [
    path('', login_required(ProductListView.as_view()), name='list'),
    path('produto-<slug:slug>', login_required(ProductDetailView.as_view()), name='detail'),
]
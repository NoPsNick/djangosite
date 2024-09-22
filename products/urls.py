from django.urls import path, include
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductListView, ProductDetailAPIView, ProductDetailView

app_name = "products"


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('', login_required(ProductListView.as_view()), name='list'),
    path('produto-<slug:slug>', login_required(ProductDetailView.as_view()), name='detail'),
    path('api/produto-<slug:slug>/', login_required(ProductDetailAPIView.as_view()), name='api-detail'),
    path('api/', include(router.urls)),
]
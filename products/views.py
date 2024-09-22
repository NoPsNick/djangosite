from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView
from django.http import Http404
from django.core.paginator import Paginator

from rest_framework import viewsets, pagination, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from cart.forms import CartAddProductForm
from pages.decorators import restrict_to_server
from .models import Product
from .serializers import ProductSerializer
from .services import get_product_from_cache, get_category_from_cache, get_cached_product_slugs, \
    get_cached_category_slugs


class ProductPagination(pagination.PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductListView(TemplateView):
    template_name = 'products/product_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Use the service to get product slugs from cache
        product_slugs = get_cached_product_slugs()

        # Use the service to fetch products from cache using their slugs
        products = [get_product_from_cache(slug) for slug in product_slugs if get_product_from_cache(slug)]

        # Filter products by category if category slug is provided in the query params
        category_slug = self.request.GET.get('category')
        if category_slug:
            category = get_category_from_cache(category_slug)
            if category:
                products = [product for product in products if product['category'] == category_slug]

        # Filter products by product slug if provided in the query params
        product_slug = self.request.GET.get('slug')
        if product_slug:
            product = get_product_from_cache(product_slug)
            products = [product] if product else []

        # Filter products by search query if provided
        search_query = self.request.GET.get('search')
        if search_query:
            products = [
                product for product in products
                if search_query.lower() in product['name'].lower() or search_query.lower() in product[
                    'description'].lower()
            ]

        # Paginate products
        paginator = Paginator(products, 6)  # 6 items per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Use the service to get category slugs from cache
        category_slugs = get_cached_category_slugs()

        # Use the service to fetch categories from cache
        categories = [get_category_from_cache(slug) for slug in category_slugs if get_category_from_cache(slug)]

        # Pass paginated products and categories to the template context
        context['products'] = page_obj
        context['categories'] = categories
        context['selected_category'] = category_slug

        return context


class ProductDetailAPIView(APIView):
    def get(self, request, slug, *args, **kwargs):
        product = cache.get(f'product_{slug}')
        if not product:
            try:
                product = Product.objects.get(slug=slug)
                cache.set(f'product_{slug}', product)
            except Product.DoesNotExist:
                return Response({'detail': 'Produto não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailView(TemplateView):
    template_name = 'products/product_detail.html'
    extra_context = {"form": CartAddProductForm()}

    def get_context_data(self, slug, **kwargs):
        context = super().get_context_data(**kwargs)

        # Use the service to get product from cache
        product = get_product_from_cache(slug)
        if not product:
            raise Http404('Produto não encontrado.')

        context['product'] = product
        return context


@method_decorator(restrict_to_server, name='dispatch')
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Override to get the full queryset for the list view, but individual products
        will be cached and retrieved from the cache in the filtering step.
        """
        product_slugs = get_cached_product_slugs()

        products = [get_product_from_cache(slug) for slug in product_slugs if get_product_from_cache(slug)]

        return products

    def list(self, request, *args, **kwargs):
        products = self.get_queryset()

        # Filter by category slug if provided
        category_slug = request.query_params.get('category', None)
        if category_slug:
            category = get_category_from_cache(category_slug)
            if category:
                products = [product for product in products if product.category == category]

        # Filter by product slug if provided
        product_slug = request.query_params.get('slug', None)
        if product_slug:
            product = get_product_from_cache(product_slug)
            products = [product] if product else []

        # Filter by search query if provided
        search_query = request.query_params.get('search', None)
        if search_query:
            products = [
                product for product in products if search_query.lower() in product.name.lower()
                                                   or search_query.lower() in product.description.lower()
            ]

        # Paginate the filtered queryset
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Return full list if pagination is not applicable
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

from django.views.generic import TemplateView
from django.http import Http404
from django.core.paginator import Paginator


from cart.forms import CartAddProductForm
from .services import get_product_from_cache, get_category_from_cache, get_cached_product_slugs, \
    get_cached_category_slugs


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
        roles = self.request.GET.get('roles')
        if roles:
            products = [product for product in products if product['is_role']]

        # Filter products by search query if provided
        search_query = self.request.GET.get('search')
        if search_query:
            products = [
                product for product in products
                if search_query.lower() in product['name'].lower() or search_query.lower() in product[
                    'description'].lower() or search_query.lower() in product['price']
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

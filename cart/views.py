from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.views.generic import TemplateView

from rest_framework.response import Response
from rest_framework.views import APIView

from products.services import get_product_from_cache
from .services import get_cart_items, get_cart, save_cart


@require_POST
def add_to_cart(request, slug):
    """
    Add a product to the cart, handling roles separately.
    """
    cart = get_cart(request)  # Retrieve the cart from cookies
    quantity = int(request.POST.get('quantity', 1))  # Default quantity

    # Get the product and check if it's a role
    product = get_product_from_cache(slug)
    is_role_product = product.get('is_role', False)

    if is_role_product:
        quantity = 1 # Roles always will be 1
        # Check for other role products in the cart
        role_products_in_cart = [
            s for s in cart if get_product_from_cache(s).get('is_role', False)
        ]
        if role_products_in_cart:
            messages.error(request, 'Não é possível adicionar mais de UM cargo ao mesmo tempo no carrinho.')
            return redirect('cart:detail')

    # Update quantity if product is already in the cart
    if slug in cart:
        cart[slug]['quantity'] = quantity
    else:
        # Add the new product to the cart
        cart[slug] = {'quantity': quantity}

    # Save the cart to cookies
    response = redirect('cart:detail')
    save_cart(response, cart)

    return response


@require_POST
def remove_from_cart(request, slug):
    cart = get_cart(request)

    if str(slug) in cart:
        del cart[str(slug)]

    response = redirect(reverse('cart:detail'))
    save_cart(response, cart)

    return response


class CartView(TemplateView):
    template_name = 'cart/cart_detail.html'

    def get(self, request, *args, **kwargs):
        cart_items, total_price = get_cart_items(request)

        return render(request, self.template_name, {
            'cart_items': cart_items,
            'total_price': total_price,
        })


class CartAPIView(APIView):
    """
    API to get the cart contents from cookies.
    """

    def get(self, request):
        cart_items, total_price = get_cart_items(request)

        # Return the cart items and total price in the response
        return Response({'cart': cart_items, 'total_price': total_price})

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework.views import APIView

from products.services import get_product_from_cache
from .services import get_cart_items, get_cart, save_cart


@require_POST
def add_to_cart(request, slug):
    """
    Add a product to the cart, and save the cart in cookies.
    """
    cart = get_cart(request)  # Retrieve the cart from cookies
    product = get_product_from_cache(slug)

    # Define the quantity (you can also get this from the POST data)
    quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not provided

    # Check if the product is already in the cart and update quantity
    if slug in cart:
        cart[slug]['quantity'] = quantity
    else:
        # Add the product to the cart
        cart[slug] = {
            'name': product['name'],
            'quantity': quantity,
        }

    # Save the updated cart back to cookies
    response = redirect('cart:detail')  # Redirect to the cart view after adding the product
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

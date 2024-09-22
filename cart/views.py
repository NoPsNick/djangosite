from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from decimal import Decimal
import json

from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework.views import APIView


from products.models import Product
from products.services import get_product_from_cache
from .forms import CartAddProductForm

# Constants for the cart cookie name
CART_COOKIE_NAME = 'cart'
CART_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def get_cart(request):
    """
    Get the cart from the cookies. The cart is stored as a JSON object in the cookies.
    """
    cart = request.COOKIES.get(CART_COOKIE_NAME)
    if cart:
        return json.loads(cart)
    return {}


def save_cart(response, cart):
    response.set_cookie(CART_COOKIE_NAME, json.dumps(cart), max_age=CART_COOKIE_MAX_AGE)


def add_to_cart(request, slug):
    """
    Add a product to the cart, and save the cart in cookies.
    """
    cart = get_cart(request)  # Retrieve the cart from cookies
    product = get_product_from_cache(slug) or get_object_or_404(Product, slug=slug)

    # Define the quantity (you can also get this from the POST data)
    quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not provided

    # Convert to Decimal
    product_price = str(product['price'])

    # Check if the product is already in the cart and update quantity
    if slug in cart:
        cart[slug]['quantity'] = quantity
        cart[slug]['total_price_product'] = str(Decimal(cart[slug]['quantity']) * Decimal(product_price))
    else:
        # Add the product to the cart
        cart[slug] = {
            'product': {
                'name': product['name'],
                'price': product_price,  # Store price as string
                'url': product['link_absoluto'],
            },
            'quantity': quantity,
            'total_price_product': str(Decimal(product_price) * quantity),  # Store total as string
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
        cart = get_cart(request)  # Get cart from cookies (no database access)
        cart_items = []

        # Iterate over the cart dictionary and build the cart items
        for slug, item in cart.items():
            cart_items.append({
                "product": {
                    'name': item['product']['name'],  # Use the name from the cookie
                    'price': item['product']['price'],  # Use the price from the cookie
                    'url': item['product']['url'],  # Product URL from the cookie
                    'slug': slug, # Product slug from the cookie
                },
                "update_quantity_form" : CartAddProductForm(
                initial={"quantity": item["quantity"], "override": True}),
                "total_price_product": item["total_price_product"],
            })

        # Calculate total price based on the data stored in the cookie
        total_price = sum(Decimal(item['total_price_product']) for item in cart_items)

        return render(request, self.template_name, {
            'cart_items': cart_items,
            'total_price': total_price,
        })


class CartAPIView(APIView):
    """
    API to get the cart contents from cookies.
    """

    def get(self, request):
        cart = get_cart(request)  # Get cart from cookies (no database access)
        cart_items = []

        # Iterate over the cart dictionary and build the cart items
        for slug, item in cart.items():
            cart_items.append({
                'product': {
                    'name': item['product']['name'],  # Use the name from the cookie
                    'price': item['product']['price'],  # Use the price from the cookie
                    'url': item['product']['url'],  # Product URL from the cookie
                    'slug': slug,
                },
                'quantity': item['quantity'],
                "total_price_product": item["total_price_product"],
            })

        # Calculate total price based on the data stored in the cookie
        total_price = sum(Decimal(item['total_price_product']) for item in cart_items)

        # Return the cart items and total price in the response
        return Response({'cart': cart_items, 'total_price': total_price})


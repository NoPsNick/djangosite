import json
from decimal import Decimal

from cart.forms import CartAddProductForm
from products.services import get_product_from_cache

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


# Retrieve the cart items from the cookie
def get_cart_items(request):
    cart = get_cart(request)  # Get cart from cookies
    cart_items = []
    # Iterate over the cart dictionary and build the cart items
    for slug, item in cart.items():
        product = get_product_from_cache(slug)
        if product:
            product_price = str(product['price'])
            total_price_product = str(Decimal(cart[slug]['quantity']) * Decimal(product_price))
            cart_items.append({
                "product": {
                    'name': item['name'],  # Use the name from the cookie
                    'price': product['price'],  # Use the price from the cache
                    'url': product['link_absoluto'],  # Product URL from the cache
                    'slug': slug,  # Product slug from the cookie
                },
                "update_quantity_form": CartAddProductForm(
                    initial={"quantity": item["quantity"], "override": True}),
                "total_price_product": str(total_price_product),
            })
    # Calculate total price based on the data stored in the cookie
    total_price = sum(Decimal(item['total_price_product']) for item in cart_items)
    return cart_items, total_price


# Save the cart items in the cookie
def save_cart_items(response, cart_items):
    response.set_cookie('cart', json.dumps(cart_items), max_age=3600*24*7)  # 1 week expiry
    return response

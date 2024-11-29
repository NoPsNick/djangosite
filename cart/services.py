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
            price = product.get('price', None)
            quantity_form = CartAddProductForm(
                initial={"quantity": item["quantity"], "override": True}
            ) if not product.get("is_role", False) else None

            product_price = str(price)
            total_price_product = str(Decimal(cart[slug]['quantity']) * Decimal(product_price))
            cart_items.append({
                "product": {
                    'name': product.get('name', None),  # Use the name from the cache
                    'price': product_price,  # Use the price from the cache
                    'url': product.get('link_absoluto', None),  # Product URL from the cache
                    'slug': slug,  # Product slug from the cookie
                    'is_role': product.get('is_role', False),
                },
                'quantity': 1 if product.get('is_role', False) else item["quantity"],
                "update_quantity_form": quantity_form,
                "total_price_product": total_price_product,
            })
    # Calculate total price based on the data stored in the cookie
    total_price = sum(Decimal(item['total_price_product']) for item in cart_items)
    return cart_items, total_price

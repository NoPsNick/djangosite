import json


# Retrieve the cart items from the cookie
def get_cart_items(request):
    cart = request.COOKIES.get('cart', '{}')
    return json.loads(cart)

# Save the cart items in the cookie
def save_cart_items(response, cart_items):
    response.set_cookie('cart', json.dumps(cart_items), max_age=3600*24*7)  # 1 week expiry
    return response

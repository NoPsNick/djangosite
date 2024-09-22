from .views import get_cart


def cart_total_quantity(request):
    cart = get_cart(request)
    return {'cart_total_quantity': len(cart)}

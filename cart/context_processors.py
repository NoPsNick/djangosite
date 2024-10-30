from .views import get_cart


def cart_info(request):
    cart = get_cart(request)
    return {'cart_info': cart}

from .views import get_cart


def cart_info(request) -> dict[str, dict[any, any]]:
    cart = get_cart(request)
    return {'cart_info': cart}

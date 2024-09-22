from django.core.cache import cache, caches
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.conf import settings

from products.models import Promotion
from users.models import User, Address, PhoneNumber
from .models import About
from .serializers import UserSerializer, PromotionSerializer, AboutSerializer


def get_user_data(user, target_userid):
    if not user or not user.is_authenticated:
        raise ValueError("User is not authenticated")

    # Attempt to fetch user instance to check if it's active
    try:
        target_user = User.objects.get(id=target_userid)
    except User.DoesNotExist:
        raise ObjectDoesNotExist("User not found")

    # Check if the target user is active, allow staff to view inactive profiles
    if not target_user.is_active and not user.is_staff:
        raise PermissionDenied("User is not active")

    # Build the cache key based on the target user's id
    cache_key = f"user_{target_userid}_profile"
    user_data = cache.get(cache_key)

    if user_data is None:
        # Serialize and cache the target user's data
        serializer = UserSerializer(target_user, context={'request': user})
        user_data = serializer.data
        cache.set(cache_key, user_data, timeout=settings.CACHE_TIMEOUT)

    return user_data



def get_abouts():
    file_cache = caches['file_based']
    abouts = file_cache.get('about_list')

    if not abouts:
        abouts_instance = About.objects.order_by('position', 'created')
        serializer = AboutSerializer(abouts_instance, many=True)
        file_cache.set('about_list', serializer.data, timeout=settings.CACHE_TIMEOUT)
        abouts = serializer.data

    return abouts


def get_promotions():
    file_cache = caches['file_based']
    promotions = file_cache.get('promotions_list')

    if not promotions:
        promotions_instance = Promotion.objects.order_by('starts_at', 'created')
        serialized_promotions = PromotionSerializer(promotions_instance, many=True).data
        file_cache.set('promotions_list', serialized_promotions, timeout=settings.CACHE_TIMEOUT)
        promotions = serialized_promotions

    return promotions


def update_promotion_cache():
    """
    Update the promotion cache with the serialized version of the product.
    :return: None
    """
    file_cache = caches['file_based']
    file_cache.delete('promotions_list')

    get_promotions()


def get_user_addresses(user):
    return Address.objects.get_user_addresses(user=user)


def get_user_numbers(user):
    return PhoneNumber.objects.get_user_phone_numbers(user=user)

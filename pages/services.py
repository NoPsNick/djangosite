from django.core.cache import cache, caches
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.conf import settings

from products.models import Promotion
from products.services import update_product_cache
from users.models import User
from .models import About
from .serializers import AboutSerializer
from products.serializers import PromotionSerializer
from users.serializers import UserSerializer


def get_user_data(current_user, target_user_id):
    """
    Retrieves user data either from the cache or the database, ensuring that
    permissions are checked, and only authorized users can access the data.
    """
    if not current_user or not current_user.is_authenticated:
        raise ValueError("User is not authenticated")

    # Try to fetch the target user object
    try:
        target_user = User.objects.get(pk=target_user_id)
    except User.DoesNotExist:
        raise ObjectDoesNotExist(f"User with ID {target_user_id} not found.")

    # Allow only staff to view inactive users
    if not target_user.is_active and not current_user.is_staff:
        raise PermissionDenied("The requested profile is inactive.")

    # Cache key for user profile data
    cache_key = f"user_{target_user_id}_profile"
    user_data = cache.get(cache_key)

    if user_data is None:
        # If data is not in the cache, serialize and cache it
        serializer = UserSerializer(target_user, context={'request': current_user})
        user_data = serializer.data
        cache.set(cache_key, user_data, timeout=settings.CACHE_TIMEOUT)

    return user_data


def get_abouts():
    file_cache = caches['file_based']
    abouts = file_cache.get('about_list')

    if not abouts:
        abouts_instance = About.objects.order_by('position', 'created')
        serializer = AboutSerializer(abouts_instance, many=True)
        file_cache.set('about_list', serializer.data, timeout=settings.HIGH_TIME_CACHE_TIMEOUT)
        abouts = serializer.data

    return abouts


def get_promotions():
    promotions = cache.get('promotions_list')

    if promotions is None:
        # Fetch from the database if the cache is empty
        promotions_instance = Promotion.objects.order_by('starts_at', 'created')
        serialized_promotions = PromotionSerializer(promotions_instance, many=True).data
        # Set promotions in cache
        cache.set('promotions_list', serialized_promotions, timeout=settings.CACHE_TIMEOUT)
        promotions = serialized_promotions

    return promotions


def update_promotion_cache(promotion):
    """
    Updates the promotion cache
    :param promotion: Promotion object that will be updated/added
    :return: None
    """
    promotions = cache.get('promotions_list')

    # If the cache is empty, regenerate only the specific promotion cache
    if promotions is None:
        promotions = get_promotions()

    # Serialize the promotion instance
    serialized_promotion = PromotionSerializer(promotion).data

    # Check if the promotion already exists in the cached list, and update it
    updated_promotions = [
        serialized_promotion if promo['id'] == promotion.id else promo for promo in promotions
    ]

    if not any(promo['id'] == promotion.id for promo in promotions):
        # If the promotion does not exist, append it
        updated_promotions.append(serialized_promotion)

    # Update the cache with the modified list
    cache.set('promotions_list', updated_promotions, timeout=settings.CACHE_TIMEOUT)
    update_product_cache(None, promotion.product)


def remove_promotion_cache(promotion):
    """
    Removes the promotion from the cache
    :param promotion: Promotion object that will be removed
    :return: None
    """
    promotions = cache.get('promotions_list')

    if promotions is None:
        # Regenerate promotions if cache is empty, avoid inconsistency
        promotions = get_promotions()

    # Filter out the promotion to be removed
    updated_promotions = [promo for promo in promotions if promo['id'] != promotion.id]

    # Update the cache with the new list
    cache.set('promotions_list', updated_promotions, timeout=settings.CACHE_TIMEOUT)


# def get_user_addresses(user):
#     return Address.objects.get_user_addresses(user=user)
#
#
# def get_user_numbers(user):
#     return PhoneNumber.objects.get_user_phone_numbers(user=user)

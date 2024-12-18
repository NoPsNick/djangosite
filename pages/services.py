from django.core.cache import cache, caches
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.conf import settings

from products.models import Promotion
from users.models import User, Role
from .models import About
from .serializers import AboutSerializer
from users.serializers import UserSerializer


def get_user_data(current_user, target_user_id):
    """
    Retrieves user data either from the cache or the database, ensuring that
    permissions are checked, and only authorized users can access the data.
    """
    if not current_user or not current_user.is_authenticated:
        raise ValueError("User is not authenticated")

    # Cache key for user profile data
    cache_key = f"user_{target_user_id}_profile"
    user_data = cache.get(cache_key)

    if user_data is None:
        target_user = User.objects.Prefetch(
                'roles',
                queryset=Role.objects.select_related('role_type'),
            ).get(id=target_user_id)
        # If data is not in the cache, serialize and cache it
        serializer = UserSerializer(target_user, context={'request': current_user})
        user_data = serializer.data
        cache.set(cache_key, user_data, timeout=getattr(settings, 'CACHE_TIMEOUT', (60 * 60 * 24 * 7)))

    if not user_data['is_active'] and not current_user.is_staff:
        raise PermissionDenied("The requested profile is inactive.")
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
    promotions = Promotion.objects.get_promotions_dict_from_cache()
    return promotions.values()


def update_promotion_cache(promotion):
    """
    Updates the promotion cache
    :param promotion: Promotion object that will be updated/added
    :return: None
    """
    Promotion.objects.update_promotion_cache(promotion.id)


def remove_promotion_cache(promotion):
    """
    Removes the promotion from the cache
    :param promotion: Promotion object that will be removed
    :return: None
    """
    Promotion.objects.delete_promotion_cache(promotion.id)

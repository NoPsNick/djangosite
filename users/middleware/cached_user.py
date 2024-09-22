from django.contrib.auth.middleware import AuthenticationMiddleware
from django.utils.functional import SimpleLazyObject
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.urls import resolve

from pages.serializers import UserSerializer

User = get_user_model()


class CachedAuthenticationMiddleware(AuthenticationMiddleware):

    def get_cache_key(self, user_id):
        return f"user_{user_id}"

    def get_user_from_cache(self, request):
        if not hasattr(request, '_cached_user'):
            user_id = request.session.get('_auth_user_id')
            if user_id:
                cache_key = self.get_cache_key(user_id)
                user = cache.get(cache_key)
                if not user:
                    # If not in cache, fetch from the database and store it
                    user_instance = User.objects.get(pk=user_id)
                    serializer = UserSerializer(user_instance, context={'request': user_instance})
                    cache.set(cache_key, serializer.data, 60 * 15)  # Cache for 15 minutes
                    user = serializer.data
                request._cached_user = user
            else:
                request._cached_user = None
        return request._cached_user

    def __call__(self, request):
        # Check if the request is for the admin site
        resolver = resolve(request.path_info)
        if resolver.namespace == 'admin':
            # Use the default AuthenticationMiddleware behavior for admin
            return super().__call__(request)

        # For other requests, apply the caching logic
        request.user = SimpleLazyObject(lambda: self.get_user_from_cache(request))
        return self.get_response(request)

from django.contrib.auth.middleware import AuthenticationMiddleware
from django.utils.functional import SimpleLazyObject
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.urls import resolve

User = get_user_model()

class CachedAuthenticationMiddleware(AuthenticationMiddleware):
    CACHE_TIMEOUT = 60 * 15  # 15 minutes for caching

    def get_cache_key(self, user_id):
        return f"user_{user_id}_auth"

    def get_user_from_cache(self, request):
        """Retrieve the full user object from cache or database."""
        if not hasattr(request, '_cached_user'):
            user_id = request.session.get('_auth_user_id')
            if user_id:
                cache_key = self.get_cache_key(user_id)
                # Try to fetch the full User instance from cache
                user = cache.get(cache_key)

                if not user:
                    # If not in cache, fetch from the database
                    try:
                        user = User.objects.get(pk=user_id)
                    except User.DoesNotExist:
                        user = None

                    # Cache the full User instance for future requests
                    if user:
                        cache.set(cache_key, user, self.CACHE_TIMEOUT)

                # Store the cached or freshly fetched User instance in request
                request._cached_user = user
            else:
                request._cached_user = None
        return request._cached_user

    def __call__(self, request):
        # Check if the request is for the admin site and bypass caching
        resolver = resolve(request.path_info)
        if resolver.namespace == 'admin':
            return super().__call__(request)

        # Apply caching for non-admin requests
        request.user = SimpleLazyObject(lambda: self.get_user_from_cache(request))
        response = self.get_response(request)

        # Clear the user cache on logout
        if not request.user.is_authenticated and '_auth_user_id' in request.session:
            self.clear_user_cache(request.session.get('_auth_user_id'))

        return response

    def clear_user_cache(self, user_id):
        """Helper to clear the cached user instance."""
        cache_key = self.get_cache_key(user_id)
        cache.delete(cache_key)

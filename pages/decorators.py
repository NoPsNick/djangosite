from functools import wraps

from django.urls import reverse, NoReverseMatch
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.core.cache import cache

import logging

from pages.middleware import track_abuse, verify_log


def restrict_to_server(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        ip = request.META.get('REMOTE_ADDR')
        if ip not in (settings.INTERNAL_IPS or ['127.0.0.1']):
            return HttpResponseForbidden("You are not allowed to access this resource.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


logger = logging.getLogger('rate_limit')

# Action weight definitions
ACTION_WEIGHTS = {
    'GET': 2,
    'POST': 3,
    'DELETE': 5,
    'PUT': 3,
}

# Maximum weight allowed in a given time window
MAX_WEIGHT = 10  # Adjust according to your needs

def strict_rate_limit(url_names=None, rate_limit_time=None):
    """Decorator to apply strict rate-limiting to views identified by URL names."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # User must be authenticated to apply strict rate-limiting
            user = request.user
            if not user.is_authenticated:
                return view_func(request, *args, **kwargs)

            if user.is_staff or user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Get the current URL path
            current_path = request.path
            # If URL names are provided, resolve them to paths and check if the current path matches
            if url_names:
                try:
                    # Resolve each URL name to a path and check if it matches the current request path
                    resolved_paths = [reverse(name, kwargs=kwargs) for name in url_names]
                except NoReverseMatch:
                    return view_func(request, *args, **kwargs)

                # If the current path doesn't match any resolved paths, bypass the rate limit
                if current_path not in resolved_paths:
                    return view_func(request, *args, **kwargs)

            # Get the request method and determine the weight
            method = request.method

            weight = ACTION_WEIGHTS.get(method, 1)

            # Create a cache key based on user ID
            key = f"strict_rate_limit_{user.id}"
            current_time, request_log, total_weight = verify_log(key)

            # Add the current request's weight to the log
            if total_weight + weight > MAX_WEIGHT:
                logger.warning(
                    f"Rate limit exceeded for key: {key}. Weight: {total_weight + weight}, Request weight: {weight}"
                )
                track_abuse(key, user.id)

                # Save the updated log with the abuse track to cache
                cache.set(key, request_log, timeout=rate_limit_time or settings.STRICT_RATE_LIMIT_TIME)
                retry_after_seconds = 60
                response = HttpResponse("Rate limit exceeded. Please wait before trying again.", status=429)
                response['Retry-After'] = retry_after_seconds
                return response

            # Update the request log with the new request
            request_log.append({'timestamp': current_time, 'weight': weight})
            cache.set(key, request_log, timeout=rate_limit_time or settings.STRICT_RATE_LIMIT_TIME)

            # Return the original view function's response
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator

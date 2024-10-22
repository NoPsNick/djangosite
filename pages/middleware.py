import hashlib
import time
import logging
from django.http import HttpResponse
from django.conf import settings
from django.core.cache import cache

# Action weight definitions
ACTION_WEIGHTS = {
    'GET': 1,
    'POST': 3,
    'DELETE': 5,
    'PUT': 3,
}

# Maximum weight allowed in a given time window (sliding window)
MAX_WEIGHT = 100
SLIDING_WINDOW_TIME = 60 * 10 # minutes

# Set up logging
logger = logging.getLogger('rate_limit')


def verify_log(key):
    cache_request_log = cache.get(key, [])
    current_time = time.time()
    # Remove outdated requests outside the sliding window
    request_log = [req for req in cache_request_log if current_time - req['timestamp'] <= SLIDING_WINDOW_TIME]
    # Calculate total weight of recent requests
    total_weight = sum(req['weight'] for req in request_log)
    return current_time, request_log, total_weight


def track_abuse(key, ip):
    """Track repeated abuse attempts and log abuse if it exceeds a threshold."""
    abuse_key = f"abuse_{key}"
    abuse_count = cache.get(abuse_key, 0)
    abuse_count += 1
    cache.set(abuse_key, abuse_count, timeout=SLIDING_WINDOW_TIME)

    if abuse_count > 3:
        logger.warning(f"Potential abuse detected from IP/user {ip} (key: {key}). Abuse count: {abuse_count}")


def get_cache_key(prefix, user_id=None, ip=None):
    key = None
    if user_id:
        key = f"{prefix}_{user_id}"
    elif ip:
        key = f"{prefix}_{hash_ip(ip)}"
    return key


def hash_ip(ip):
    """Hash IP for rate-limiting anonymous users by IP address."""
    return hashlib.sha256(ip.encode()).hexdigest()


class RateLimitMiddlewareBase:
    """
    Middleware base for rate limiting with sliding window.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def is_rate_limited(key, rate_limit_time, weight=1):
        """
        Check if the user has exceeded the rate limit based on their request weight.
        """
        # Get the request log from the cache
        current_time, request_log, total_weight = verify_log(key)

        # If the weight exceeds the max, log and return a rate limit violation
        if total_weight + weight > MAX_WEIGHT:
            logger.warning(
                f"Rate limit exceeded for key: {key}. Total weight: {total_weight}, Request weight: {weight}")
            request_log.append({'timestamp': current_time, 'weight': weight})
            cache.set(key, request_log, timeout=rate_limit_time)
            return True

        # Add current request to the log
        request_log.append({'timestamp': current_time, 'weight': weight})
        cache.set(key, request_log, timeout=rate_limit_time)

        return False


class GeneralRateLimitMiddleware(RateLimitMiddlewareBase):
    def __call__(self, request):
        user = request.user
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        hashed_ip = hash_ip(ip)

        # Determine the weight of the current request based on method
        method = request.method
        weight = ACTION_WEIGHTS.get(method, 1)

        if not user.is_anonymous:
            key = get_cache_key('rate_limit', user_id=user.id)
            rate_limit_time = settings.GENERAL_RATE_LIMIT_TIME
        else:
            key = get_cache_key('rate_limit_anonymous', ip=hashed_ip)
            rate_limit_time = getattr(settings, 'ANONYMOUS_RATE_LIMIT_TIME', settings.GENERAL_RATE_LIMIT_TIME)

        # Check if rate limit is exceeded
        if self.is_rate_limited(key, rate_limit_time, weight=weight):
            logger.info(
                f"Rate limit exceeded for user {user.id if user.is_authenticated else 'Anonymous'}, IP {ip}, Method {
                method}, Path {request.path}")

            # Track possible abuse attempts
            track_abuse(key, ip)
            retry_after_seconds = 20
            response = HttpResponse("Rate limit exceeded. Please wait before trying again.", status=429)
            response['Retry-After'] = retry_after_seconds
            return response

        # Log request duration for performance monitoring
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        logger.info(f"Request to {request.path} took {duration:.3f} seconds")

        return response

import hashlib
import logging
from datetime import datetime

logger = logging.getLogger('user_activity')

def hash_ip(ip):
    return hashlib.sha256(ip.encode()).hexdigest()


class LogUserActionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log user actions
        user = getattr(request, 'user', None)  # Safely get 'user' attribute

        if user and user.is_authenticated:
            logger.info(f'[{datetime.now()}]User {user.username} accessed {request.path}')
        else:
            logger.info(f'[{datetime.now()}]Anonymous user accessed {request.path} from hashed IP '
                        f'{hash_ip(request.META.get("REMOTE_ADDR"))}')

        return response
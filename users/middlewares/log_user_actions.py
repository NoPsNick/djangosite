import logging

logger = logging.getLogger('user_activity')


class LogUserActionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log user actions
        user = getattr(request, 'user', None)

        if user and user.is_authenticated:
            logger.info(f'User {user.username} accessed {request.path}')
        else:
            logger.info(f'Anonymous user accessed {request.path} from IP '
                        f'{(request.META.get("REMOTE_ADDR"))}')

        return response
from django import template

register = template.Library()


@register.simple_tag
def url_startswith(request_path, prefix, user_id=None):
    """
    Check if the current request path starts with a given prefix.
    If `user_id` is provided, remove it from the `prefix` before checking.
    """
    if user_id:
        # Reassign the result of replace to remove the user_id from the URL path
        prefix = prefix.replace(f"{user_id}/", '')
    return request_path.startswith(prefix)
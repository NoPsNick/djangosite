from audioop import reverse

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        # Redirect to the user's profile after login
        user_id = request.user.id
        return reverse('pages:profile', kwargs={"user_id": user_id})

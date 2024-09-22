from django.urls import reverse
from django.test import TestCase, Client
from users.models import User
from unittest.mock import patch
from django.core.cache import cache


class PerfilPageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        self.profile_url_1 = reverse('pages:profile', kwargs={'user_id': self.user1.pk})
        self.profile_url_2 = reverse('pages:profile', kwargs={'user_id': self.user2.pk})
        self.user_manager = User.objects

    def test_user_can_see_own_profile(self):
        self.client.login(username='user1', password='password1')
        response = self.client.get(self.profile_url_1)
        self.assertEqual(response.status_code, 200)
        # Adjust this string to reflect the actual content shown on the profile page
        self.assertContains(response, self.user1.username)

    def test_user_cannot_see_other_users_profile(self):
        self.client.login(username='user1', password='password1')
        response = self.client.get(self.profile_url_2)
        self.assertEqual(response.status_code, 403)  # Ensure your view is raising PermissionDenied

    def test_unauthenticated_user_redirect(self):
        response = self.client.get(self.profile_url_1)
        # Assuming you redirect unauthenticated users to login page
        self.assertEqual(response.status_code, 302)  # Redirect to log in
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.profile_url_1}")

    def test_nonexistent_user_profile(self):
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse('pages:profile', kwargs={'user_id': 0}))
        self.assertEqual(response.status_code, 403)

    def test_profile_data_cached(self):
        self.client.login(username='user1', password='password1')

        # Clear the cache for the target user
        cache_key = f"user_{self.user1.id}_profile"
        cache.delete(cache_key)

        # First request (no cache, should hit the database)
        with patch('users.models.User.objects.get') as mock_get:
            mock_get.return_value = self.user1
            response = self.client.get(self.profile_url_1)
            self.assertEqual(response.status_code, 302)
            mock_get.assert_called_once()  # Database should be hit for the first request

        # # Ensure the user data is cached after the first request
        # cached_user_data = cache.get(cache_key)
        # self.assertIsNotNone(cached_user_data, "User data should be cached after the first request.")

        # Second request (should use cache)
        with patch('users.models.User.objects.get') as mock_get:
            response = self.client.get(self.profile_url_1)
            self.assertEqual(response.status_code, 302)
            mock_get.assert_not_called()  # Database should not be hit, cache should be used

    def test_inactive_user_profile_access(self):
        self.user1.is_active = False
        self.user1.save()
        self.assertEqual(self.user1.is_active, False)

        self.client.login(username='user1', password='password1')
        response = self.client.get(self.profile_url_1)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Não foi possível acessar esta página", status_code=403)

    def test_cache_expires_and_fetches_new_data(self):
        self.client.login(username='user1', password='password1')

        # First request to cache data
        response = self.client.get(self.profile_url_1)
        self.assertEqual(response.status_code, 200)

        # Expire the cache manually using the correct cache key logic
        cache_key = self.user_manager.get_cache_key(self.user1.id)
        cache.delete(cache_key)

        # Fetch the profile again, should hit the database now
        with patch('users.models.User.objects.get') as mock_get:
            mock_get.return_value = self.user1
            response = self.client.get(self.profile_url_1)
            self.assertEqual(response.status_code, 200)
            mock_get.assert_called()

    def test_sensitive_information_not_exposed(self):
        self.client.login(username='user1', password='password1')
        response = self.client.get(self.profile_url_1)
        self.assertEqual(response.status_code, 200)

        # Check that password field is not in the response content
        self.assertNotContains(response, self.user1.password)

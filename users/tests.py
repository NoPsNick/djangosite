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
        self.profile_url_1 = reverse('pages:profile', kwargs={'user_id': self.user1.id})
        self.profile_url_2 = reverse('pages:profile', kwargs={'user_id': self.user2.id})
        self.user_manager = User.objects

    def test_user_can_see_own_profile(self):
        # Log in the user
        login_successful = self.client.login(username='user1', password='password1')
        self.assertTrue(login_successful, "Login should be successful.")

        # Access profile page
        response = self.client.get(self.profile_url_1)

        # Assert 302 OK status
        self.assertEqual(response.status_code, 302)
        self.assertContains(response, self.user1.username)

    def test_user_cannot_see_other_users_profile(self):
        # Log in as user1
        self.client.login(username='user1', password='password1')

        # Try accessing user2's profile
        response = self.client.get(self.profile_url_2)

        # Assert 403 Forbidden status
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_user_redirect(self):
        # Access the profile page without logging in
        response = self.client.get(self.profile_url_1)

        # Assert 302 redirect status
        self.assertEqual(response.status_code, 302)

        # Assert correct redirect to login page
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.profile_url_1}")

    def test_nonexistent_user_profile(self):
        # Log in as user1
        self.client.login(username='user1', password='password1')

        # Try accessing a non-existent user's profile (user_id=0)
        response = self.client.get(reverse('pages:profile', kwargs={'user_id': 0}))

        # Assert 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_profile_data_cached(self):
        # Log in as user1
        self.client.login(username='user1', password='password1')

        # Cache key for user1's profile
        cache_key = f"user_{self.user1.id}_profile"
        cache.delete(cache_key)  # Clear the cache

        # First request (should hit the database)
        with patch('users.models.User.objects.get') as mock_get:
            mock_get.return_value = self.user1
            response = self.client.get(self.profile_url_1)
            self.assertEqual(response.status_code, 302)
            mock_get.assert_called_once()  # Database is queried

        # Simulate that the profile data is now cached
        cache.set(cache_key, self.user1)

        # Second request (should NOT hit the database)
        with patch('users.models.User.objects.get') as mock_get:
            response = self.client.get(self.profile_url_1)
            self.assertEqual(response.status_code, 302)
            mock_get.assert_not_called()  # Cache is used

    def test_inactive_user_profile_access(self):
        # Create an inactive user
        self.user1.is_active = False
        self.user1.save()

        # Attempt to log in with the inactive user
        login_successful = self.client.login(username='user1', password='password1')
        self.assertTrue(login_successful, "Login should be attempted.")

        # Try accessing the profile page
        response = self.client.get(self.profile_url_1)

        # Assert that the response is a redirect to the account inactive page
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('account_inactive'))  # Adjust this to your actual inactive account URL

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
            self.assertEqual(response.status_code, 302)
            mock_get.assert_called()

    def test_sensitive_information_not_exposed(self):
        self.client.login(username='user1', password='password1')
        response = self.client.get(self.profile_url_1)
        self.assertEqual(response.status_code, 302)

        # Check that password field is not in the response content
        self.assertNotContains(response, self.user1.password)

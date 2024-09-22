import time

from django.test import TestCase
from django.urls import reverse
from users.models import User
from django.core.cache import cache


class RateLimitMiddlewareTests(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.address_add_url = reverse('pages:address_add')  # Adjust based on your URL configuration

    def tearDown(self):
        # Clear the cache after each test to avoid interference
        cache.clear()

    def test_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(self.address_add_url)  # Simulate a POST request
        self.assertEqual(response.status_code, 302)  # Check if it returns the original view (no rate limiting)
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(self.address_add_url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_within_rate_limit(self):
        response = self.client.post(self.address_add_url)
        self.assertEqual(response.status_code, 200)  # Expecting the form to be valid and processed

    def test_authenticated_user_exceeding_rate_limit(self):
        # Simulate multiple requests to exceed the rate limit
        for _ in range(3):  # Adjust based on your defined MAX_WEIGHT
            self.client.post(self.address_add_url)

        # Make another request that should exceed the rate limit
        response = self.client.post(self.address_add_url)
        self.assertEqual(response.status_code, 429)  # Check for rate limit exceeded response

    def test_authenticated_user_after_rate_limit_exceeded(self):
        # Exceed the rate limit
        for _ in range(2):
            self.client.post(self.address_add_url)

        # Checking if the limit wasn't exceeded yet
        response = self.client.post(self.address_add_url)
        self.assertEqual(response.status_code, 200)

        self.client.post(self.address_add_url)  # This should exceed the limit
        response = self.client.post(self.address_add_url)
        self.assertEqual(response.status_code, 429)

        # Now, wait for some time or clear the cache to simulate the expiration
        cache.delete(f'strict_rate_limit_{self.user.id}') # or wait for cache to expire based on your settings
        # time.sleep(20)

        # Now, try again
        response = self.client.post(self.address_add_url)
        self.assertEqual(response.status_code, 200)  # Should now be able to make a valid request again

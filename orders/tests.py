from django.test import TestCase
from django.urls import reverse
from users.models import User
from django.core.cache import cache


class RateLimitMiddlewareTests(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.order_list = reverse('orders:order_list')  # Adjust based on your URL configuration

    def tearDown(self):
        # Clear the cache after each test to avoid interference
        cache.clear()

    def test_unauthenticated_user(self):
        self.client.login(username='testuser', password='testpass')
        self.client.logout()
        response = self.client.get(self.order_list)  # Simulate a GET request
        self.assertEqual(response.status_code, 302)  # Check if it returns the original view (no rate limiting)
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.order_list)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_within_rate_limit(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.order_list)
        self.assertEqual(response.status_code, 200)  # Expecting the form to be valid and processed

    def test_authenticated_user_exceeding_rate_limit(self):
        self.client.login(username='testuser', password='testpass')
        # Simulate multiple requests to exceed the rate limit
        for _ in range(10):  # Adjust based on your defined MAX_WEIGHT
            self.client.get(self.order_list)

        # Make another request that should exceed the rate limit
        response = self.client.get(self.order_list)
        self.assertEqual(response.status_code, 429)  # Check for rate limit exceeded response

    def test_authenticated_user_after_rate_limit_exceeded(self):
        self.client.login(username='testuser', password='testpass')
        # Exceed the rate limit
        for _ in range(4):
            self.client.get(self.order_list)

        # Checking if the limit wasn't exceeded yet
        response = self.client.get(self.order_list)
        self.assertEqual(response.status_code, 200)

        self.client.get(self.order_list)  # This should exceed the limit
        response = self.client.get(self.order_list)
        self.assertEqual(response.status_code, 429)

        # Now, wait for some time or clear the cache to simulate the expiration
        cache.delete(f'strict_rate_limit_{self.user.id}') # or wait for cache to expire based on your settings
        # time.sleep(20)

        # Now, try again
        response = self.client.get(self.order_list)
        self.assertEqual(response.status_code, 200)  # Should now be able to make a valid request again
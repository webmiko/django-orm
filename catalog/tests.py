"""Catalog app tests."""

from django.test import Client, TestCase
from django.urls import reverse


class HomeViewTest(TestCase):
    """Tests for home view."""

    def test_home_returns_200(self):
        client = Client()
        response = client.get(reverse("catalog:home"))
        self.assertEqual(response.status_code, 200)

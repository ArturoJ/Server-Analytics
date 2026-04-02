"""Tests de la vista del dashboard."""
from django.test import TestCase


class DashboardViewTest(TestCase):

    def test_renderiza(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Dashboard')

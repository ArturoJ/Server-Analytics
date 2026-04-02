"""Tests de la vista de servidores."""
from django.test import TestCase

from ..helpers import DatosTestMixin


class ServidoresViewTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_renderiza(self):
        resp = self.client.get('/servidores/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'test-server')

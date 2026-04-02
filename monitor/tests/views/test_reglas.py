"""Tests de la vista de reglas de deteccion."""
from django.test import TestCase

from ..helpers import DatosTestMixin


class ReglasViewTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_renderiza(self):
        resp = self.client.get('/reglas/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'test-scan')

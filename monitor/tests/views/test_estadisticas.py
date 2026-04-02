"""Tests de la vista de estadisticas por pais."""
from django.test import TestCase


class EstadisticasViewTest(TestCase):

    def test_renderiza(self):
        resp = self.client.get('/estadisticas/paises/')
        self.assertEqual(resp.status_code, 200)

"""Tests del endpoint /api/estadisticas/paises/."""
import json

from django.test import TestCase

from ..helpers import DatosTestMixin


class ApiEstadisticasPaisesTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_respuesta_ok(self):
        resp = self.client.get('/api/estadisticas/paises/')
        self.assertEqual(resp.status_code, 200)

    def test_ranking(self):
        data = json.loads(self.client.get('/api/estadisticas/paises/').content)
        self.assertEqual(data['total_paises'], 1)
        self.assertEqual(data['ranking'][0]['codigo'], 'DE')
        self.assertEqual(data['ranking'][0]['peticiones'], 15)

    def test_franjas_horarias(self):
        data = json.loads(self.client.get('/api/estadisticas/paises/').content)
        self.assertEqual(len(data['franjas']), 6)
        self.assertEqual(len(data['por_franja']), 1)

"""Tests del endpoint /api/reglas/."""
import json

from django.test import TestCase

from ..helpers import DatosTestMixin


class ApiReglasTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_respuesta_ok(self):
        resp = self.client.get('/api/reglas/')
        self.assertEqual(resp.status_code, 200)

    def test_reglas_con_stats(self):
        data = json.loads(self.client.get('/api/reglas/').content)
        self.assertEqual(len(data['reglas']), 1)
        regla = data['reglas'][0]
        self.assertEqual(regla['nombre'], 'test-scan')
        self.assertIn('disparos_hoy', regla)
        self.assertIn('ips_hoy', regla)

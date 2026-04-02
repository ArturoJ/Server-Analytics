"""Tests del endpoint /api/dashboard/."""
import json

from django.test import TestCase

from ..helpers import DatosTestMixin


class ApiDashboardTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_respuesta_ok(self):
        resp = self.client.get('/api/dashboard/')
        self.assertEqual(resp.status_code, 200)

    def test_estructura_json(self):
        resp = self.client.get('/api/dashboard/')
        data = json.loads(resp.content)
        self.assertIn('kpis', data)
        self.assertIn('por_hora', data)
        self.assertIn('por_tipo', data)
        self.assertIn('top_ips', data)
        self.assertIn('ultimos', data)

    def test_kpis_correctos(self):
        resp = self.client.get('/api/dashboard/')
        kpis = json.loads(resp.content)['kpis']
        self.assertEqual(kpis['total_ips'], 1)
        self.assertEqual(kpis['total_peticiones'], 15)
        self.assertEqual(kpis['paises'], 1)
        self.assertIn('visitantes', kpis)

    def test_filtro_desde_invalido(self):
        """Con parametro desde invalido devuelve todo el acumulado."""
        resp = self.client.get('/api/dashboard/?desde=invalido')
        kpis = json.loads(resp.content)['kpis']
        self.assertEqual(kpis['total_peticiones'], 15)

    def test_solo_get(self):
        resp = self.client.post('/api/dashboard/')
        self.assertEqual(resp.status_code, 405)

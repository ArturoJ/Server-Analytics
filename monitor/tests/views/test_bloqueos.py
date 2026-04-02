"""Tests de las vistas de bloqueos: lista y detalle de IP."""
from django.test import TestCase

from ..helpers import DatosTestMixin


class BloquesListaViewTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_renderiza(self):
        resp = self.client.get('/bloqueos/')
        self.assertEqual(resp.status_code, 200)


class DetalleIpViewTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_ip_valida(self):
        resp = self.client.get('/bloqueos/10.0.0.1/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '10.0.0.1')

    def test_ip_invalida(self):
        """Una IP con caracteres invalidos no rompe la pagina."""
        resp = self.client.get('/bloqueos/invalid<script>/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Sin registros')

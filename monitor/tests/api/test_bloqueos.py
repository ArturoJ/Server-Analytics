"""Tests del endpoint /api/bloqueos/."""
import json

from django.test import TestCase

from ..helpers import DatosTestMixin


class ApiBloquesTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_respuesta_ok(self):
        resp = self.client.get('/api/bloqueos/')
        self.assertEqual(resp.status_code, 200)

    def test_paginacion(self):
        resp = self.client.get('/api/bloqueos/?page=1')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['page'], 1)
        self.assertEqual(len(data['items']), 1)

    def test_filtro_motivo(self):
        resp = self.client.get('/api/bloqueos/?motivo=escaneo')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 1)

    def test_filtro_motivo_sin_resultados(self):
        resp = self.client.get('/api/bloqueos/?motivo=fuerza_bruta')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 0)

    def test_filtro_pais(self):
        resp = self.client.get('/api/bloqueos/?pais=DE')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 1)

    def test_filtro_min_pet(self):
        resp = self.client.get('/api/bloqueos/?min_pet=100')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 0)

    def test_export_csv(self):
        resp = self.client.get('/api/bloqueos/?formato=csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')
        self.assertIn('bloqueos.csv', resp['Content-Disposition'])

    def test_pagina_invalida(self):
        resp = self.client.get('/api/bloqueos/?page=abc')
        data = json.loads(resp.content)
        self.assertEqual(data['page'], 1)

    def test_pagina_negativa(self):
        """Una pagina negativa se trata como pagina 1."""
        resp = self.client.get('/api/bloqueos/?page=-5')
        data = json.loads(resp.content)
        self.assertEqual(data['page'], 1)

    def test_pagina_muy_alta(self):
        """Una pagina que supera el total devuelve items vacios."""
        resp = self.client.get('/api/bloqueos/?page=99999')
        data = json.loads(resp.content)
        self.assertEqual(len(data['items']), 0)

    def test_min_pet_invalido(self):
        """Un min_pet no numerico se ignora y devuelve todo."""
        resp = self.client.get('/api/bloqueos/?min_pet=abc')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 1)

    def test_filtros_combinados(self):
        """Motivo + pais se aplican juntos."""
        resp = self.client.get('/api/bloqueos/?motivo=escaneo&pais=DE')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 1)

    def test_filtros_combinados_sin_resultado(self):
        resp = self.client.get('/api/bloqueos/?motivo=escaneo&pais=US')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 0)

    def test_csv_contenido_correcto(self):
        """El CSV contiene las cabeceras y los datos del bloqueo."""
        resp = self.client.get('/api/bloqueos/?formato=csv')
        contenido = resp.content.decode('utf-8')
        self.assertIn('Fecha,Hora,IP', contenido)
        self.assertIn('10.0.0.1', contenido)
        self.assertIn('Alemania', contenido)

    def test_csv_respeta_filtros(self):
        """El CSV respeta los filtros aplicados."""
        resp = self.client.get('/api/bloqueos/?formato=csv&motivo=fuerza_bruta')
        contenido = resp.content.decode('utf-8')
        self.assertNotIn('10.0.0.1', contenido)

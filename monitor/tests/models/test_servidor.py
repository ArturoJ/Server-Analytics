"""Tests del modelo Servidor."""
from django.test import TestCase

from monitor.models import Servidor


class ServidorTest(TestCase):

    def test_crear_servidor(self):
        s = Servidor.objects.create(nombre='vps-01', ip='10.0.0.1')
        self.assertEqual(str(s), 'vps-01')
        self.assertEqual(s.estado, 'activo')

    def test_nombre_unico(self):
        Servidor.objects.create(nombre='vps-01', ip='10.0.0.1')
        with self.assertRaises(Exception):
            Servidor.objects.create(nombre='vps-01', ip='10.0.0.2')

    def test_estado_por_defecto(self):
        s = Servidor.objects.create(nombre='vps-02', ip='10.0.0.2')
        self.assertEqual(s.estado, 'activo')

    def test_campos_opcionales_vacios(self):
        s = Servidor.objects.create(nombre='vps-03', ip='10.0.0.3')
        self.assertEqual(s.hostname, '')
        self.assertEqual(s.sistema_operativo, '')

    def test_fecha_alta_automatica(self):
        s = Servidor.objects.create(nombre='vps-04', ip='10.0.0.4')
        self.assertIsNotNone(s.fecha_alta)

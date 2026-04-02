"""Tests del modelo ReglaDeteccion."""
from django.test import TestCase

from monitor.models import ReglaDeteccion


class ReglaDeteccionTest(TestCase):

    def test_crear_regla(self):
        r = ReglaDeteccion.objects.create(
            nombre='scan-01', patron='/wp-admin', tipo='escaneo',
        )
        self.assertEqual(str(r), 'scan-01')
        self.assertTrue(r.activa)
        self.assertEqual(r.umbral_peticiones, 10)

    def test_tipos_validos(self):
        for tipo in ['escaneo', 'fuerza_bruta', 'exceso', 'custom']:
            r = ReglaDeteccion.objects.create(
                nombre=f'regla-{tipo}', patron='.*', tipo=tipo,
            )
            self.assertEqual(r.tipo, tipo)

"""Tests del modelo Bloqueo."""
from django.test import TestCase
from django.utils import timezone

from monitor.models import Bloqueo
from ..helpers import DatosTestMixin


class BloqueoTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_crear_bloqueo(self):
        self.assertEqual(str(self.bloqueo), '10.0.0.1 (Escaneo de vulnerabilidades)')
        self.assertTrue(self.bloqueo.activo)

    def test_bloqueo_sin_regla(self):
        b = Bloqueo.objects.create(
            servidor=self.servidor, ip='10.0.0.2',
            motivo='exceso', peticiones=100,
            fecha_bloqueo=timezone.now(),
        )
        self.assertIsNone(b.regla)

    def test_rutas_json(self):
        self.assertEqual(len(self.bloqueo.rutas), 2)
        self.assertIn('404 /wp-admin', self.bloqueo.rutas)

    def test_ordering(self):
        """Los bloqueos mas recientes van primero."""
        b2 = Bloqueo.objects.create(
            servidor=self.servidor, ip='10.0.0.3',
            motivo='escaneo', peticiones=5,
            fecha_bloqueo=timezone.now(),
        )
        primero = Bloqueo.objects.first()
        self.assertEqual(primero.pk, b2.pk)

    def test_relacion_servidor(self):
        self.assertEqual(self.servidor.bloqueos.count(), 1)

    def test_rutas_vacias_por_defecto(self):
        b = Bloqueo.objects.create(
            servidor=self.servidor, ip='10.0.0.4',
            motivo='escaneo', peticiones=1,
            fecha_bloqueo=timezone.now(),
        )
        self.assertEqual(b.rutas, [])

    def test_cascade_al_borrar_servidor(self):
        """Al borrar un servidor, sus bloqueos se eliminan."""
        self.servidor.delete()
        self.assertEqual(Bloqueo.objects.count(), 0)

    def test_set_null_al_borrar_regla(self):
        """Al borrar una regla, el bloqueo mantiene regla=None."""
        self.regla.delete()
        self.bloqueo.refresh_from_db()
        self.assertIsNone(self.bloqueo.regla)

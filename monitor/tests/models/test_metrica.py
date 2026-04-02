"""Tests del modelo MetricaDiaria."""
from django.test import TestCase
from django.utils import timezone

from monitor.models import MetricaDiaria
from ..helpers import DatosTestMixin


class MetricaDiariaTest(DatosTestMixin, TestCase):

    def setUp(self):
        self.crear_datos()

    def test_crear_metrica(self):
        m = MetricaDiaria.objects.create(
            servidor=self.servidor, fecha=timezone.now().date(),
            total_bloqueos=10, total_peticiones=500,
        )
        self.assertIn('test-server', str(m))

    def test_unique_together(self):
        hoy = timezone.now().date()
        MetricaDiaria.objects.create(servidor=self.servidor, fecha=hoy)
        with self.assertRaises(Exception):
            MetricaDiaria.objects.create(servidor=self.servidor, fecha=hoy)

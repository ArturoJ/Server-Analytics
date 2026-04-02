"""Tests del modelo Visita."""
from django.test import TestCase

from monitor.models import Visita


class VisitaTest(TestCase):

    def test_crear_visita(self):
        v = Visita.objects.create(ip='1.2.3.4')
        self.assertEqual(str(v), '1.2.3.4')
        self.assertEqual(v.peticiones, 1)

    def test_ip_unica(self):
        Visita.objects.create(ip='1.2.3.4')
        with self.assertRaises(Exception):
            Visita.objects.create(ip='1.2.3.4')

    def test_incremento_peticiones_con_f(self):
        """El incremento atomico con F() funciona correctamente."""
        from django.db.models import F
        Visita.objects.create(ip='5.6.7.8', peticiones=1)
        Visita.objects.filter(ip='5.6.7.8').update(peticiones=F('peticiones') + 3)
        v = Visita.objects.get(ip='5.6.7.8')
        self.assertEqual(v.peticiones, 4)

    def test_ordering_por_ultima_visita(self):
        """Las visitas mas recientes van primero."""
        v1 = Visita.objects.create(ip='1.1.1.1')
        v2 = Visita.objects.create(ip='2.2.2.2')
        primero = Visita.objects.first()
        self.assertEqual(primero.ip, '2.2.2.2')

    def test_primera_visita_automatica(self):
        v = Visita.objects.create(ip='9.9.9.9')
        self.assertIsNotNone(v.primera_visita)

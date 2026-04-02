"""Tests de los modelos del dashboard modular: Dashboard, CardModule, CardInstance."""
from django.test import TestCase

from monitor.models import Dashboard, CardModule, CardInstance


class DashboardTest(TestCase):

    def test_dashboard(self):
        d = Dashboard.objects.create(nombre='Principal')
        self.assertEqual(str(d), 'Principal')


class CardModuleTest(TestCase):

    def test_crear_modulo(self):
        m = CardModule.objects.create(slug='kpi', nombre='KPI')
        self.assertEqual(str(m), 'KPI')
        self.assertTrue(m.activo)


class CardInstanceTest(TestCase):

    def setUp(self):
        self.dash = Dashboard.objects.create(nombre='Test')
        self.module = CardModule.objects.create(slug='kpi', nombre='KPI')

    def test_crear_instancia(self):
        c = CardInstance.objects.create(dashboard=self.dash, module=self.module)
        self.assertEqual(c.display_name, 'KPI')
        self.assertIsNotNone(c.instance_id)

    def test_label_personalizado(self):
        c = CardInstance.objects.create(dashboard=self.dash, module=self.module, label='Mi KPI')
        self.assertEqual(c.display_name, 'Mi KPI')

    def test_config_json(self):
        c = CardInstance.objects.create(dashboard=self.dash, module=self.module, config={'tipo': 'ips'})
        c.refresh_from_db()
        self.assertEqual(c.config['tipo'], 'ips')

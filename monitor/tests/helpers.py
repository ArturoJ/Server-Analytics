"""Datos de prueba reutilizables para todos los tests."""
from django.utils import timezone

from monitor.models import Servidor, ReglaDeteccion, Bloqueo


class DatosTestMixin:
    """Crea datos base para los tests: servidor, regla y bloqueo."""

    def crear_datos(self):
        self.servidor = Servidor.objects.create(
            nombre='test-server', ip='192.168.1.1',
            sistema_operativo='Ubuntu 22.04',
        )
        self.regla = ReglaDeteccion.objects.create(
            nombre='test-scan', patron='/wp-admin|/.env',
            tipo='escaneo', umbral_peticiones=5, ventana_minutos=5,
        )
        self.bloqueo = Bloqueo.objects.create(
            servidor=self.servidor, regla=self.regla,
            ip='10.0.0.1', pais='Alemania', codigo_pais='DE',
            motivo='escaneo', peticiones=15,
            rutas=['404 /wp-admin', '404 /.env'],
            fecha_bloqueo=timezone.now(),
        )

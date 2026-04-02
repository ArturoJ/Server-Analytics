"""Tests de servicios: CardRegistry, geoip, sanitizar_ruta y codigo_a_bandera."""
from django.test import TestCase

from monitor.services import CardRegistry, buscar_pais
from monitor.models import CardModule
from monitor.api.dashboard import codigo_a_bandera
from monitor.management.commands.analizar_logs import sanitizar_ruta


class CardRegistryDiscoverTest(TestCase):

    def test_descubre_7_cards(self):
        """Descubre las 7 carpetas de cards."""
        cards = CardRegistry.discover()
        slugs = [c['slug'] for c in cards]
        self.assertIn('kpi', slugs)
        self.assertIn('grafico_hora', slugs)
        self.assertIn('tabla_bloqueos', slugs)
        self.assertEqual(len(cards), 7)


class CardRegistryFilesTest(TestCase):

    def test_get_template(self):
        tpl = CardRegistry.get_template('kpi')
        self.assertIsNotNone(tpl)
        self.assertTrue(tpl.exists())

    def test_get_style(self):
        style = CardRegistry.get_style('kpi')
        self.assertIsNotNone(style)

    def test_get_script(self):
        script = CardRegistry.get_script('kpi')
        self.assertIsNotNone(script)

    def test_slug_inexistente(self):
        self.assertIsNone(CardRegistry.get_template('no-existe'))

    def test_path_traversal(self):
        """Un slug malicioso no escapa del directorio de cards."""
        self.assertIsNone(CardRegistry.get_template('../../etc/passwd'))


class CardRegistrySyncTest(TestCase):

    def test_sync_crea_modulos(self):
        """sync_to_db crea los CardModule en la BD."""
        CardRegistry.sync_to_db()
        self.assertEqual(CardModule.objects.filter(activo=True).count(), 7)

    def test_sync_desactiva_borrados(self):
        """Si un modulo ya no tiene carpeta, se desactiva."""
        CardModule.objects.create(slug='fantasma', nombre='Fantasma', activo=True)
        CardRegistry.sync_to_db()
        fantasma = CardModule.objects.get(slug='fantasma')
        self.assertFalse(fantasma.activo)


# ============================================================
# Tests de sanitizar_ruta
# ============================================================

class SanitizarRutaTest(TestCase):

    def test_ruta_normal(self):
        self.assertEqual(sanitizar_ruta('/wp-admin'), '/wp-admin')

    def test_strip_tags(self):
        """Elimina tags HTML para prevenir XSS."""
        self.assertNotIn('<script>', sanitizar_ruta('<script>alert(1)</script>/admin'))

    def test_elimina_comillas(self):
        result = sanitizar_ruta('ruta"con\'comillas`raras')
        self.assertNotIn('"', result)
        self.assertNotIn("'", result)
        self.assertNotIn('`', result)

    def test_solo_ascii_printable(self):
        """Elimina caracteres no imprimibles."""
        result = sanitizar_ruta('/ruta\x00\x01\x02normal')
        self.assertEqual(result, '/rutanormal')

    def test_trunca_a_200(self):
        ruta_larga = '/a' * 200
        result = sanitizar_ruta(ruta_larga)
        self.assertEqual(len(result), 200)

    def test_string_vacio(self):
        self.assertEqual(sanitizar_ruta(''), '')


# ============================================================
# Tests de codigo_a_bandera
# ============================================================

class CodigoABanderaTest(TestCase):

    def test_codigo_valido(self):
        bandera = codigo_a_bandera('ES')
        self.assertTrue(len(bandera) > 0)

    def test_codigo_vacio(self):
        self.assertEqual(codigo_a_bandera(''), '')

    def test_codigo_none(self):
        self.assertEqual(codigo_a_bandera(None), '')

    def test_codigo_un_caracter(self):
        self.assertEqual(codigo_a_bandera('E'), '')

    def test_codigo_tres_caracteres(self):
        self.assertEqual(codigo_a_bandera('ESP'), '')

    def test_minusculas(self):
        """Funciona igual con minusculas."""
        self.assertEqual(codigo_a_bandera('es'), codigo_a_bandera('ES'))


# ============================================================
# Tests de geoip (buscar_pais)
# ============================================================

class GeoipTest(TestCase):

    def test_ip_invalida(self):
        """Una IP invalida devuelve tupla vacia sin errores."""
        pais, codigo = buscar_pais('no-es-una-ip')
        self.assertEqual(pais, '')
        self.assertEqual(codigo, '')

    def test_ip_privada(self):
        """Una IP privada no tiene pais."""
        pais, codigo = buscar_pais('192.168.1.1')
        self.assertEqual(pais, '')
        self.assertEqual(codigo, '')

    def test_ip_localhost(self):
        pais, codigo = buscar_pais('127.0.0.1')
        self.assertEqual(pais, '')
        self.assertEqual(codigo, '')

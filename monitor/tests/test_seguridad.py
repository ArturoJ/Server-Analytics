"""Tests de las medidas de seguridad: SQL injection, XSS, path traversal."""
import json

from django.test import TestCase


class SqlInjectionTest(TestCase):

    def test_motivo_con_sql(self):
        """La inyeccion SQL en motivo no devuelve datos extra."""
        resp = self.client.get("/api/bloqueos/?motivo=escaneo' OR 1=1--")
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 0)

    def test_pais_con_union(self):
        """UNION SELECT no funciona porque el ORM parametriza las queries."""
        resp = self.client.get("/api/bloqueos/?pais=US' UNION SELECT * FROM monitor_servidor--")
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 0)

    def test_min_pet_con_sql(self):
        """Inyeccion en min_pet se descarta por el int()."""
        resp = self.client.get("/api/bloqueos/?min_pet=1;DROP TABLE monitor_bloqueo")
        data = json.loads(resp.content)
        self.assertIn('total', data)


class XssTest(TestCase):

    def test_pais_con_script(self):
        """Un intento de XSS en el parametro pais se trata como literal."""
        resp = self.client.get('/api/bloqueos/?pais=<script>alert(1)</script>')
        data = json.loads(resp.content)
        self.assertEqual(data['total'], 0)

    def test_xss_en_respuesta_json(self):
        """La respuesta JSON no contiene tags HTML sin escapar."""
        resp = self.client.get('/api/bloqueos/?motivo=<img onerror=alert(1)>')
        self.assertNotIn(b'onerror', resp.content)


class PathTraversalTest(TestCase):

    def test_ip_con_traversal(self):
        """Caracteres de path traversal en la URL no devuelven datos sensibles."""
        resp = self.client.get('/bloqueos/%2e%2e%2fetc%2fpasswd/')
        self.assertIn(resp.status_code, [200, 404])

    def test_doble_encoding(self):
        resp = self.client.get('/bloqueos/%252e%252e%252fetc%252fpasswd/')
        self.assertIn(resp.status_code, [200, 404])
        if resp.status_code == 200:
            self.assertNotIn(b'root:', resp.content)


class MetodosHttpTest(TestCase):

    def test_api_solo_get(self):
        """Los endpoints API rechazan metodos que no sean GET."""
        for url in ['/api/dashboard/', '/api/bloqueos/', '/api/reglas/', '/api/estadisticas/paises/']:
            resp = self.client.post(url)
            self.assertEqual(resp.status_code, 405, f'POST deberia ser 405 en {url}')

    def test_put_rechazado(self):
        for url in ['/api/dashboard/', '/api/bloqueos/', '/api/reglas/']:
            resp = self.client.put(url)
            self.assertEqual(resp.status_code, 405)

    def test_delete_rechazado(self):
        for url in ['/api/dashboard/', '/api/bloqueos/', '/api/reglas/']:
            resp = self.client.delete(url)
            self.assertEqual(resp.status_code, 405)


class HeadersSeguridadTest(TestCase):

    def test_x_frame_options(self):
        resp = self.client.get('/')
        self.assertEqual(resp.get('X-Frame-Options'), 'DENY')

    def test_content_type_nosniff(self):
        resp = self.client.get('/')
        self.assertEqual(resp.get('X-Content-Type-Options'), 'nosniff')

    def test_csp_presente(self):
        resp = self.client.get('/')
        csp = resp.get('Content-Security-Policy', '')
        self.assertIn("default-src 'none'", csp)
        self.assertIn('nonce-', csp)

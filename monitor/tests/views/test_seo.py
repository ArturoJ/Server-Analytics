"""Tests de paginas auxiliares: SEO, PWA y honeypot."""
import json

from django.test import TestCase


class RobotsTxtTest(TestCase):

    def test_renderiza(self):
        resp = self.client.get('/robots.txt')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertContains(resp, 'User-agent')


class SitemapXmlTest(TestCase):

    def test_renderiza(self):
        resp = self.client.get('/sitemap.xml')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/xml')
        self.assertContains(resp, '<urlset')


class ContactoHoneypotTest(TestCase):

    def test_get(self):
        resp = self.client.get('/contacto/')
        self.assertEqual(resp.status_code, 200)

    def test_post_honeypot(self):
        """El honeypot acepta POST y devuelve JSON de exito sin hacer nada."""
        resp = self.client.post('/contacto/', data={'name': 'bot', 'message': 'spam'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'ok')


class Error404Test(TestCase):

    def test_ruta_inexistente(self):
        resp = self.client.get('/ruta-que-no-existe/')
        self.assertEqual(resp.status_code, 404)
